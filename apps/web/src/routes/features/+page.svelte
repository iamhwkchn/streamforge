<script lang="ts">
	import { onMount } from 'svelte';
	import {
		getAllFeatures,
		runQuery,
		deleteFeature,
		type FeatureWithDataset,
		type QueryResult
	} from '$lib/api';

	let features = $state<FeatureWithDataset[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	let runningId = $state<string | null>(null);
	let resultsById = $state<Record<string, QueryResult>>({});
	let errorsById = $state<Record<string, string>>({});

	let deletingId = $state<string | null>(null);
	let confirmDeleteId = $state<string | null>(null);
	let deleteError = $state<string | null>(null);

	onMount(async () => {
		try {
			features = await getAllFeatures();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load features';
		} finally {
			loading = false;
		}
	});

	async function runFeature(f: FeatureWithDataset) {
		runningId = f.id;
		errorsById = { ...errorsById, [f.id]: '' };
		try {
			resultsById = { ...resultsById, [f.id]: await runQuery(f.sql_definition) };
		} catch (e) {
			errorsById = { ...errorsById, [f.id]: e instanceof Error ? e.message : 'Query failed' };
		} finally {
			runningId = null;
		}
	}

	function closeOutput(featureId: string) {
		const { [featureId]: _r, ...restResults } = resultsById;
		resultsById = restResults;
		const { [featureId]: _e, ...restErrors } = errorsById;
		errorsById = restErrors;
	}

	async function confirmDelete(featureId: string) {
		deletingId = featureId;
		deleteError = null;
		try {
			await deleteFeature(featureId);
			features = features.filter((f) => f.id !== featureId);
			closeOutput(featureId);
		} catch (e) {
			deleteError = e instanceof Error ? e.message : 'Failed to delete feature';
		} finally {
			deletingId = null;
			confirmDeleteId = null;
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
		<p class="mt-1 text-sm text-gray-500">All feature definitions registered in the catalog.</p>
	</div>

	{#if deleteError}
		<div class="mb-4 rounded-md bg-red-50 p-4 text-sm text-red-700">{deleteError}</div>
	{/if}

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
	{:else if features.length === 0}
		<p class="text-sm text-gray-500">No features registered yet.</p>
	{:else}
		<div class="space-y-4">
			{#each features as f}
				{@const result = resultsById[f.id]}
				{@const runError = errorsById[f.id]}
				<div class="rounded-lg border border-gray-200 bg-white shadow-sm">
					<div class="flex items-center justify-between border-b border-gray-100 px-5 py-3">
						<div class="flex items-center gap-2">
							<span class="font-medium text-gray-900">{f.name}</span>
							<span class="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">{f.dataset_name}</span>
						</div>
						<div class="flex items-center gap-3">
							<span class="text-xs text-gray-400">{fmt(f.created_at)}</span>
							<button
								onclick={() => runFeature(f)}
								disabled={runningId === f.id}
								class="flex items-center gap-1.5 rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
							>
								{#if runningId === f.id}
									<svg class="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
										<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
										<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
									</svg>
									Running…
								{:else}
									<svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-4.586-2.651A1 1 0 009 9.382v5.236a1 1 0 001.166.986l4.586-2.651a1 1 0 000-1.785z" />
									</svg>
									Run
								{/if}
							</button>
							{#if confirmDeleteId === f.id}
								<span class="text-xs text-gray-500">Delete?</span>
								<button
									onclick={() => confirmDelete(f.id)}
									disabled={deletingId === f.id}
									class="rounded-md bg-red-600 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
								>
									{deletingId === f.id ? '…' : 'Yes'}
								</button>
								<button
									onclick={() => (confirmDeleteId = null)}
									class="rounded-md px-2.5 py-1.5 text-xs font-medium text-gray-500 hover:bg-gray-50"
								>
									No
								</button>
							{:else}
								<button
									onclick={() => (confirmDeleteId = f.id)}
									title="Delete feature"
									class="rounded-md p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600"
								>
									<svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
									</svg>
								</button>
							{/if}
						</div>
					</div>
					<div class="p-5">
						<pre class="overflow-x-auto rounded bg-gray-50 p-3 font-mono text-xs text-gray-700 leading-relaxed">{f.sql_definition}</pre>
					</div>

					{#if runError}
						<div class="mx-5 mb-5">
							<div class="mb-2 flex justify-end">
								<button
									onclick={() => closeOutput(f.id)}
									class="text-xs font-medium text-gray-400 hover:text-gray-600"
								>
									Close ✕
								</button>
							</div>
							<div class="rounded-md bg-red-50 p-3 font-mono text-xs text-red-700">{runError}</div>
						</div>
					{:else if result}
						<div class="mx-5 mb-5">
							<div class="mb-2 flex items-center justify-between">
								<span class="text-xs text-gray-400">
									{result.row_count.toLocaleString()} row{result.row_count === 1 ? '' : 's'}
									{result.has_more ? ' (more available)' : ''}
								</span>
								<button
									onclick={() => closeOutput(f.id)}
									class="text-xs font-medium text-gray-400 hover:text-gray-600"
								>
									Close ✕
								</button>
							</div>
							<div class="overflow-auto rounded-lg border border-gray-200">
								<table class="min-w-full divide-y divide-gray-200 text-sm">
									<thead class="bg-gray-50">
										<tr>
											{#each result.columns as col}
												<th class="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500 whitespace-nowrap">
													{col}
												</th>
											{/each}
										</tr>
									</thead>
									<tbody class="divide-y divide-gray-100 bg-white">
										{#each result.rows as row}
											<tr class="hover:bg-gray-50">
												{#each row as cell}
													<td class="px-4 py-2 font-mono text-xs text-gray-700 whitespace-nowrap max-w-xs truncate">
														{#if cell == null}<span class="text-gray-300">null</span>{:else}{String(cell)}{/if}
													</td>
												{/each}
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
