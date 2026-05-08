<script lang="ts">
	import { onMount } from 'svelte';
	import { getDatasets, getFeatures, type Dataset, type Feature } from '$lib/api';

	let datasets = $state<Dataset[]>([]);
	let selectedId = $state<string>('');
	let features = $state<Feature[]>([]);
	let loadingDatasets = $state(true);
	let loadingFeatures = $state(false);
	let error = $state<string | null>(null);

	onMount(async () => {
		try {
			datasets = await getDatasets();
			if (datasets.length > 0) {
				selectedId = datasets[0].id;
				await loadFeatures();
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load';
		} finally {
			loadingDatasets = false;
		}
	});

	async function loadFeatures() {
		if (!selectedId) return;
		loadingFeatures = true;
		error = null;
		try {
			features = await getFeatures(selectedId);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load features';
			features = [];
		} finally {
			loadingFeatures = false;
		}
	}

	function fmt(iso: string) {
		return new Date(iso).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}
</script>

<div class="p-8">
	<div class="mb-6">
		<h1 class="text-2xl font-semibold text-gray-900">Features</h1>
		<p class="mt-1 text-sm text-gray-500">Feature definitions registered in the catalog.</p>
	</div>

	{#if loadingDatasets}
		<div class="flex items-center gap-2 text-sm text-gray-500">
			<svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
			</svg>
			Loading…
		</div>
	{:else}
		<!-- Dataset selector -->
		<div class="mb-6">
			<label for="dataset-select" class="mb-1.5 block text-sm font-medium text-gray-700">
				Dataset
			</label>
			<select
				id="dataset-select"
				bind:value={selectedId}
				onchange={loadFeatures}
				class="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
			>
				{#each datasets as ds}
					<option value={ds.id}>{ds.name}</option>
				{/each}
			</select>
		</div>

		{#if error}
			<div class="rounded-md bg-red-50 p-4 text-sm text-red-700">{error}</div>
		{:else if loadingFeatures}
			<div class="flex items-center gap-2 text-sm text-gray-500">
				<svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
					<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
				</svg>
				Loading features…
			</div>
		{:else if features.length === 0}
			<p class="text-sm text-gray-500">No features registered for this dataset.</p>
		{:else}
			<div class="space-y-4">
				{#each features as f}
					<div class="rounded-lg border border-gray-200 bg-white shadow-sm">
						<div class="flex items-center justify-between border-b border-gray-100 px-5 py-3">
							<span class="font-medium text-gray-900">{f.name}</span>
							<span class="text-xs text-gray-400">{fmt(f.created_at)}</span>
						</div>
						<div class="p-5">
							<pre class="overflow-x-auto rounded bg-gray-50 p-3 font-mono text-xs text-gray-700 leading-relaxed">{f.sql_definition}</pre>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	{/if}
</div>
