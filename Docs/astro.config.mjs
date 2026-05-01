// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import react from '@astrojs/react';

import mermaid from 'astro-mermaid';

const site = process.env.SITE_URL ?? 'https://kdai-docs.vercel.app';

// https://astro.build/config
export default defineConfig({
	site,
	integrations: [
		react(),
		mermaid({

			theme: 'forest',
			autoTheme: true
		}),

		starlight({
			title: 'KDAI Documentation',
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/W-KDAI/kdai2' }],
			components: {
				Footer: './src/components/DocsFooter.astro',
			},
		}),
	],
});
