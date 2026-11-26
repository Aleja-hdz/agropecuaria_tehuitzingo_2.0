/*
  Warnings:

  - A unique constraint covering the columns `[slug]` on the table `species` will be added. If there are existing duplicate values, this will fail.
  - Added the required column `updated_at` to the `products` table without a default value. This is not possible if the table is not empty.
  - Added the required column `slug` to the `species` table without a default value. This is not possible if the table is not empty.

*/
-- DropForeignKey
ALTER TABLE "products" DROP CONSTRAINT "products_brand_id_fkey";

-- AlterTable
ALTER TABLE "products" ADD COLUMN     "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN     "updated_at" TIMESTAMP(3) NOT NULL,
ALTER COLUMN "brand_id" DROP NOT NULL;

-- AlterTable
ALTER TABLE "species" ADD COLUMN     "slug" TEXT NOT NULL;

-- CreateIndex
CREATE INDEX "products_category_id_idx" ON "products"("category_id");

-- CreateIndex
CREATE INDEX "products_brand_id_idx" ON "products"("brand_id");

-- CreateIndex
CREATE INDEX "products_is_active_is_published_idx" ON "products"("is_active", "is_published");

-- CreateIndex
CREATE UNIQUE INDEX "species_slug_key" ON "species"("slug");

-- AddForeignKey
ALTER TABLE "products" ADD CONSTRAINT "products_brand_id_fkey" FOREIGN KEY ("brand_id") REFERENCES "brands"("id") ON DELETE SET NULL ON UPDATE CASCADE;
