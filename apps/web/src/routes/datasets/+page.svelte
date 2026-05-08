<script lang="ts">
	import { onMount } from 'svelte';
	import { getDatasets, type Dataset } from '$lib/api';

	let datasets = $state<Dataset[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	onMount(async () => {
		try {
			datasets = await getDatasets();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load datasets';
		} finally {
			loading = false;
		}
	});

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
		<h1 class="text-2xl font-semibold text-gray-900">Datasets</h1>
		<p class="mt-1 text-sm text-gray-500">All datasets registered in the metadata catalog.</p>
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
	{:else if datasets.length === 0}
		<div class="text-sm text-gray-500">No datasets found.</div>
	{:else}
		<div class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
			<table class="min-w-full divide-y divide-gray-200">
				<thead class="bg-gray-50">
					<tr>
						<th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Name</th>
						<th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Storage Location</th>
						<th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Created</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-200 bg-white">
					{#each datasets as ds}
						<tr class="hover:bg-gray-50">
							<td class="px-6 py-4">
								<a
									href="/datasets/{ds.id}"
									class="font-medium text-indigo-600 hover:text-indigo-800"
								>
									{ds.name}
								</a>
							</td>
							<td class="px-6 py-4 font-mono text-xs text-gray-500">{ds.storage_location}</td>
							<td class="px-6 py-4 text-sm text-gray-500">{fmt(ds.created_at)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>
