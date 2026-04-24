import rss from "@astrojs/rss";
import { getCollection } from "astro:content";
import { getConfigurationCollection } from "../lib/utils";

export async function GET() {
	const { data: config } = await getConfigurationCollection();
	const posts = await getCollection("blog");
	const siteUrl = config.site.baseUrl.toString().replace(/\/$/, "");

	return rss({
		title: config.globalMeta.title,
		description: config.globalMeta.description,
		site: siteUrl,
		items: posts
			.sort((a, b) => b.data.timestamp.valueOf() - a.data.timestamp.valueOf())
			.map((post) => ({
				title: post.data.title,
				description: post.data.description,
				pubDate: post.data.timestamp,
				link: `${siteUrl}/posts/${post.data.slug}`,
			})),
	});
}
