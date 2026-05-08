<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { getDatasets, getPartitions, getFeatures, type Dataset, type Partition, type Feature } from '$lib/api';

	const id = $derived($page.params.id ?? '');

	let dataset = $state<Dataset | null>(null);
	let partitions = $state<Partition[]>([]);
	let features = $state<Feature[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let activeTab = $state<'partitions' | 'features'>('partitions');

	onMount(async () => {
		if (!id) return;
		try {
			const [datasets, parts, feats] = await Promise.all([
				getDatasets(),
				getPartitions(id),
				getFeatures(id)
			]);
			dataset = datasets.find((d) => d.id === id) ?? null;
			partitions = parts;
			features = feats;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load dataset';
		} finally {
			loading = false;
		}
	});

	function fmt(iso: string) {
		return new Date(iso).toLocaleString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function fmtRows(n: number | null) {
		if (n == null) return '—';
		return n.toLocaleString();
	}
</script>

<div class="p-8">
	<div class="mb-2">
		<a href="/datasets" class="text-sm text-indigo-600 hover:text-indigo-800">← Datasets</a>
	</div>

	{#if loading}
		<div class="flex items-center gap-2 text-sm text-gray-500">
			<svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
			</svg>
			Loading…
		</div>
	{:else if error}
		<div class="rounded-md bg-red-50 p-4 text-sm text-red-700">{error}</div>
	{:else}
		<div class="mb-6">
			<h1 class="text-2xl font-semibold text-gray-900">{dataset?.name ?? id}</h1>
			{#if dataset}
				<p class="mt-1 font-mono text-xs text-gray-400">{dataset.storage_location}</p>
			{/if}
		</div>

		<!-- Tabs -->
		<div class="mb-6 border-b border-gray-200">
			<nav class="-mb-px flex gap-6">
				<button
					onclick={() => (activeTab = 'partitions')}
					class="pb-3 text-sm font-medium {activeTab === 'partitions'
						? 'border-b-2 border-indigo-600 text-indigo-600'
						: 'text-gray-500 hover:text-gray-700'}"
				>
					Partitions ({partitions.length})
				</button>
				<button
					onclick={() => (activeTab = 'features')}
					class="pb-3 text-sm font-medium {activeTab === 'features'
						? 'border-b-2 border-indigo-600 text-indigo-600'
						: 'text-gray-500 hover:text-gray-700'}"
				>
					Features ({features.length})
				</button>
			</nav>
		</div>

		{#if activeTab === 'partitions'}
			{#if partitions.length === 0}
				<p class="text-sm text-gray-500">No partitions registered yet.</p>
			{:else}
				<div class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
					<table class="min-w-full divide-y divide-gray-200">
						<thead class="bg-gray-50">
							<tr>
								<th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Path</th>
								<th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Rows</th>
								<th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Processed</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-200 bg-white">
							{#each partitions as p}
								<tr class="hover:bg-gray-50">
									<td class="px-6 py-4 font-mono text-xs text-gray-700">{p.partition_path}</td>
									<td class="px-6 py-4 text-sm text-gray-600">{fmtRows(p.row_count)}</td>
									<td class="px-6 py-4 text-sm text-gray-500">{fmt(p.processed_at)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		{:else}
			{#if features.length === 0}
				<p class="text-sm text-gray-500">No features registered yet.</p>
			{:else}
				<div class="space-y-3">
					{#each features as f}
						<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
							<div class="mb-2 flex items-center justify-between">
								<span class="font-medium text-gray-900">{f.name}</span>
								<span class="text-xs text-gray-400">{fmt(f.created_at)}</span>
							</div>
							<pre class="overflow-x-auto rounded bg-gray-50 p-3 font-mono text-xs text-gray-700">{f.sql_definition}</pre>
						</div>
					{/each}
				</div>
			{/if}
		{/if}
	{/if}
</div>
