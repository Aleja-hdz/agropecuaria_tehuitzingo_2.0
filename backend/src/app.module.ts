import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { PrismaModule } from './prisma/prisma.module';
import { ProductsModule } from './modules/products/products.module';
import { CategoriesModule } from './modules/categories/categories.module';
import { BrandsModule } from './modules/brands/brands.module';
import { SpeciesModule } from './modules/species/species.module';

@Module({
  imports: [PrismaModule, ProductsModule, CategoriesModule, BrandsModule, SpeciesModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
