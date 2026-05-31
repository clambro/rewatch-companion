import type { ImageMetadata } from "astro";

const imageAssets = import.meta.glob<{ default: ImageMetadata }>(
  "/src/assets/images/**/*.{jpg,jpeg,png,webp}",
  { eager: true },
);

export function imageAssetFor(src: string): ImageMetadata {
  const assetPath = `/src/assets${src}`;
  const asset = imageAssets[assetPath]?.default;

  if (!asset) {
    throw new Error(`Missing image asset for ${src}. Expected ${assetPath}.`);
  }

  return asset;
}
