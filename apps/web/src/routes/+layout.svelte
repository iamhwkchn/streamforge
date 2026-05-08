<script lang="ts">
	import './layout.css';
	import { page } from '$app/stores';

	let { children } = $props();

	const nav = [
		{
			href: '/datasets',
			label: 'Datasets',
			icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 7c0-1.657 3.582-3 8-3s8 1.343 8 3M4 7v5c0 1.657 3.582 3 8 3s8-1.343 8-3V7M4 12v5c0 1.657 3.582 3 8 3s8-1.343 8-3v-5" />`
		},
		{
			href: '/query',
			label: 'Query',
			icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />`
		},
		{
			href: '/features',
			label: 'Features',
			icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 6h16M4 10h16M4 14h10" />`
		}
	];
</script>

<div class="flex h-screen overflow-hidden bg-gray-50 font-sans">
	<aside class="flex w-56 flex-col bg-slate-900 text-slate-100">
		<div class="flex items-center gap-2 border-b border-slate-700 px-4 py-5">
			<svg class="h-5 w-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
			</svg>
			<span class="text-sm font-semibold tracking-wide">StreamForge</span>
		</div>

		<nav class="flex-1 space-y-0.5 p-3">
			{#each nav as link}
				{@const active = $page.url.pathname.startsWith(link.href)}
				<a
					href={link.href}
					class="flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors {active
						? 'bg-slate-700 text-white'
						: 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'}"
				>
					<svg class="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						{@html link.icon}
					</svg>
					{link.label}
				</a>
			{/each}
		</nav>

		<div class="border-t border-slate-700 px-4 py-3">
			<p class="text-xs text-slate-500">Stage 1 — Local Lakehouse</p>
		</div>
	</aside>

	<main class="flex-1 overflow-auto">
		{@render children()}
	</main>
</div>
