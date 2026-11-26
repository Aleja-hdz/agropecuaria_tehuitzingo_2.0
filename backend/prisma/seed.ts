import 'dotenv/config';
import { PrismaPg } from '@prisma/adapter-pg';
import { PrismaClient } from '../generated/prisma/client';

const adapter = new PrismaPg({
  connectionString: process.env.DATABASE_URL,
});

const prisma = new PrismaClient({ adapter });

function toSlug(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

async function seedCategories() {
  const rootCategories = [
    { name: 'Alimentos balanceados', slug: 'alimentos-balanceados' },
    { name: 'Medicamentos veterinarios', slug: 'medicamentos-veterinarios' },
    { name: 'Productos para mascotas', slug: 'productos-para-mascotas' },
    { name: 'Implementos', slug: 'implementos' },
  ];

  const categoryMap = new Map<string, string>();

  for (const cat of rootCategories) {
    const record = await prisma.category.upsert({
      where: { slug: cat.slug },
      update: { name: cat.name },
      create: {
        name: cat.name,
        slug: cat.slug,
        parentId: null,
      },
    });
    categoryMap.set(cat.slug, record.id);
  }

  const subcategories: Array<{
    name: string;
    slug: string;
    parentSlug: string;
  }> = [
    // Alimentos balanceados
    {
      name: 'Alimentos para producción',
      slug: 'alimentos-para-produccion',
      parentSlug: 'alimentos-balanceados',
    },
    {
      name: 'Alimentos para engorda',
      slug: 'alimentos-para-engorda',
      parentSlug: 'alimentos-balanceados',
    },
    {
      name: 'Aves de combate',
      slug: 'aves-de-combate',
      parentSlug: 'alimentos-balanceados',
    },

    // Medicamentos veterinarios
    {
      name: 'Antibióticos y antimicrobianos',
      slug: 'antibioticos-y-antimicrobianos',
      parentSlug: 'medicamentos-veterinarios',
    },
    {
      name: 'Desparasitantes y antihelmínticos',
      slug: 'desparasitantes-y-antihelminticos',
      parentSlug: 'medicamentos-veterinarios',
    },
    {
      name: 'Biológicos y vacunas',
      slug: 'biologicos-y-vacunas',
      parentSlug: 'medicamentos-veterinarios',
    },
    {
      name: 'Vitaminas, electrolitos y suplementos',
      slug: 'vitaminas-electrolitos-y-suplementos',
      parentSlug: 'medicamentos-veterinarios',
    },
    {
      name: 'Antiinflamatorios y manejo de heridas',
      slug: 'antiinflamatorios-y-manejo-de-heridas',
      parentSlug: 'medicamentos-veterinarios',
    },

    // Productos para mascotas
    {
      name: 'Alimento para mascotas',
      slug: 'alimento-para-mascotas',
      parentSlug: 'productos-para-mascotas',
    },
    {
      name: 'Accesorios para mascotas',
      slug: 'accesorios-para-mascotas',
      parentSlug: 'productos-para-mascotas',
    },

    // Implementos
    {
      name: 'Comederos, bebederos y mamilas',
      slug: 'comederos-bebederos-y-mamilas',
      parentSlug: 'implementos',
    },
    {
      name: 'Jaulas, voladeros y corrales',
      slug: 'jaulas-voladeros-y-corrales',
      parentSlug: 'implementos',
    },
    {
      name: 'Monturas, cuerdas y aperos',
      slug: 'monturas-cuerdas-y-aperos',
      parentSlug: 'implementos',
    },
    {
      name: 'Herramientas y equipo',
      slug: 'herramientas-y-equipo',
      parentSlug: 'implementos',
    },
  ];

  for (const sub of subcategories) {
    const parentId = categoryMap.get(sub.parentSlug) ?? null;
    await prisma.category.upsert({
      where: { slug: sub.slug },
      update: {
        name: sub.name,
        parentId,
      },
      create: {
        name: sub.name,
        slug: sub.slug,
        parentId,
      },
    });
  }
}

async function seedSpecies() {
  const speciesNames = [
    'Bovinos',
    'Equinos',
    'Porcinos',
    'Caprinos',
    'Ovinos',
    'Aviar',
    'Canino',
    'Felino',
    'Aquacultura',
    'Apícola',
    'Roedores',
    'Reptilia',
    'Cúnicos',
    'Aves ornamentales',
  ];

  for (const name of speciesNames) {
    const slug = toSlug(name);
    await prisma.species.upsert({
      where: { slug },
      update: { name },
      create: { name, slug },
    });
  }
}

async function seedBrands() {
  const brandNames = [
    'Apiaba',
    'Fasa',
    'Nutre bien',
    'Unión',
    'AGROVET',
    'ARANDA',
    'Aranda Pets',
    'Dechra',
    'Laboratorios Pier',
    'PANAVET',
    'PROVETMEX',
    'Riverfarma',
    'Sanfer',
    'Zoetis',
    'Pedigree',
    'Whiskas',
    'Perron',
    'Ganador',
    'Minino',
    'Poder Canino',
    'Super-cria',
    'comprovet',
    'Implementos López',
  ];

  for (const name of brandNames) {
    const slug = toSlug(name);
    await prisma.brand.upsert({
      where: { slug },
      update: { name },
      create: { name, slug },
    });
  }
}

async function main() {
  console.log('Iniciando seed de Agropecuaria Tehuitzingo 2.0...');
  await seedCategories();
  await seedSpecies();
  await seedBrands();
  console.log('Seed completado correctamente.');
}

main()
  .catch((error) => {
    console.error('Error ejecutando el seed:', error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });