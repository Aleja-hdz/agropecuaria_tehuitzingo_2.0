import { Injectable, NotFoundException } from '@nestjs/common';
import { Prisma } from '../../../generated/prisma/client';
import { PrismaService } from '../../prisma/prisma.service';
import { GetProductsDto } from './dto/get-products.dto';

@Injectable()
export class ProductsService {
  constructor(private readonly prisma: PrismaService) {}

  private readonly productInclude = {
    category: true,
    brand: true,
    productSpecies: {
      include: {
        species: true,
      },
    },
    productImages: {
      include: {
        image: true,
      },
      orderBy: [{ isPrimary: 'desc' as const }, { sortOrder: 'asc' as const }],
    },
  };

  async findAll(query: GetProductsDto) {
    const page = query.page ?? 1;
    const limit = query.limit ?? 12;
    const skip = (page - 1) * limit;

    const where: Prisma.ProductWhereInput = {
      isActive: true,
      isPublished: true,
    };

    if (query.search?.trim()) {
      const term = query.search.trim();
      where.OR = [
        { name: { contains: term, mode: 'insensitive' } },
        { sku: { contains: term, mode: 'insensitive' } },
      ];
    }

    if (query.category?.trim()) {
      const categorySlug = query.category.trim();
      where.category = {
        OR: [{ slug: categorySlug }, { parent: { slug: categorySlug } }],
      };
    }

    if (query.brand?.trim()) {
      where.brand = {
        slug: query.brand.trim(),
      };
    }

    if (query.species?.trim()) {
      where.productSpecies = {
        some: {
          species: {
            slug: query.species.trim(),
          },
        },
      };
    }

    const orderByMap: Record<string, Prisma.ProductOrderByWithRelationInput[]> = {
      newest: [{ createdAt: 'desc' }, { name: 'asc' }],
      name_asc: [{ name: 'asc' }],
      name_desc: [{ name: 'desc' }],
    };
    const orderBy = orderByMap[query.sort ?? 'newest'];

    const [total, items] = await Promise.all([
      this.prisma.product.count({ where }),
      this.prisma.product.findMany({
        where,
        skip,
        take: limit,
        include: this.productInclude,
        orderBy,
      }),
    ]);

    const data = items.map((product) => ({
      ...product,
      species: product.productSpecies.map((item) => item.species),
      images: product.productImages.map((item) => ({
        ...item.image,
        isPrimary: item.isPrimary,
        sortOrder: item.sortOrder,
      })),
    }));

    return {
      data,
      meta: {
        total,
        page,
        limit,
        totalPages: Math.ceil(total / limit) || 1,
      },
    };
  }

  async findBySlug(slug: string) {
    const product = await this.prisma.product.findFirst({
      where: {
        slug,
        isActive: true,
        isPublished: true,
      },
      include: this.productInclude,
    });

    if (!product) {
      throw new NotFoundException(`Producto con slug "${slug}" no encontrado`);
    }

    return {
      ...product,
      species: product.productSpecies.map((item) => item.species),
      images: product.productImages.map((item) => ({
        ...item.image,
        isPrimary: item.isPrimary,
        sortOrder: item.sortOrder,
      })),
    };
  }
}