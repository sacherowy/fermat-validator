import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/admin/", "/my-solutions", "/login"],
    },
    sitemap: "https://fermat-validator.pl/sitemap.xml",
  };
}
