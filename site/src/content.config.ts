import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const contentBase = "../content/shows";
const articleSections = ["themes", "characters"] as const;

const listedArticle = z.object({
  title: z.string(),
  path: z.string(),
});

const seo = z.object({
  title: z.string(),
  description: z.string(),
});

const shows = defineCollection({
  loader: glob({
    base: contentBase,
    pattern: "*/show.yaml",
    generateId: ({ entry }) => entry.replace(/\/show\.ya?ml$/, ""),
  }),
  schema: z.object({
    title: z.string(),
    slug: z.string(),
    about: listedArticle.optional(),
    themes: z.array(listedArticle).optional(),
    characters: z.array(listedArticle).optional(),
    seasons: z.array(
      z.object({
        season: z.number(),
        episodes: z.array(
          z.object({
            code: z.string(),
            title: z.string(),
            path: z.string(),
          }),
        ),
      }),
    ),
  }),
});

const episodeMetadata = defineCollection({
  loader: glob({
    base: contentBase,
    pattern: "*/episodes/*/*/episode.yaml",
    generateId: ({ entry }) => entry.replace(/\/episode\.ya?ml$/, ""),
  }),
  schema: z.object({
    show: z.string(),
    season: z.number(),
    episode: z.number(),
    code: z.string(),
    title: z.string(),
    slug: z.string(),
    seo,
  }),
});

const episodeArticles = defineCollection({
  loader: glob({
    base: contentBase,
    pattern: "*/episodes/*/*/index.mdx",
    generateId: ({ entry }) => entry.replace(/\/index\.mdx$/, ""),
  }),
  schema: z.object({
    title: z.string(),
    dek: z.string().optional(),
  }),
});

const articleMetadata = defineCollection({
  loader: glob({
    base: contentBase,
    pattern: [
      "*/about/article.yaml",
      `*/{${articleSections.join(",")}}/*/article.yaml`,
    ],
    generateId: ({ entry }) => entry.replace(/\/article\.ya?ml$/, ""),
  }),
  schema: z.object({
    show: z.string(),
    title: z.string(),
    slug: z.string().optional(),
    seo,
  }),
});

const articleArticles = defineCollection({
  loader: glob({
    base: contentBase,
    pattern: [
      "*/about/index.mdx",
      `*/{${articleSections.join(",")}}/*/index.mdx`,
    ],
    generateId: ({ entry }) => entry.replace(/\/index\.mdx$/, ""),
  }),
  schema: z.object({
    title: z.string(),
    dek: z.string().optional(),
  }),
});

export const collections = {
  shows,
  episodeMetadata,
  episodeArticles,
  articleMetadata,
  articleArticles,
};
