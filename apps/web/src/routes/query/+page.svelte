<script lang="ts">
	import { runQuery, type QueryResult } from '$lib/api';

	let sql = $state('SELECT * FROM minio.retail.retail_events LIMIT 10');
	let result = $state<QueryResult | null>(null);
	let error = $state<string | null>(null);
	let running = $state(false);

	async function execute() {
		if (!sql.trim()) return;
		running = true;
		error = null;
		result = null;
		try {
			result = await runQuery(sql);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Query failed';
		} finally {
			running = false;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
			execute();
		}
	}
</script>

<div class="flex h-full flex-col p-8">
	<div class="mb-6">
		<h1 class="text-2xl font-semibold text-gray-900">SQL Query</h1>
		<p class="mt-1 text-sm text-gray-500">Execute SQL against Trino. Press ⌘ Enter to run.</p>
	</div>

	<!-- Editor -->
	<div class="mb-4 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
		<div class="border-b border-gray-100 bg-gray-50 px-4 py-2">
			<span class="text-xs font-medium text-gray-400 uppercase tracking-wide">SQL</span>
		</div>
		<textarea
			bind:value={sql}
			onkeydown={handleKeydown}
			rows={6}
			spellcheck={false}
			class="w-full resize-none p-4 font-mono text-sm text-gray-800 outline-none placeholder-gray-300"
			placeholder="SELECT ..."
		></textarea>
	</div>

	<div class="mb-6 flex items-center gap-3">
		<button
			onclick={execute}
			disabled={running}
			class="flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
		>
			{#if running}
				<svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
					<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
				</svg>
				Running…
			{:else}
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-4.586-2.651A1 1 0 009 9.382v5.236a1 1 0 001.166.986l4.586-2.651a1 1 0 000-1.785z" />
				</svg>
				Run
			{/if}
		</button>
		{#if result}
			<span class="text-xs text-gray-400">
				{result.row_count.toLocaleString()} row{result.row_count === 1 ? '' : 's'}
				{result.has_more ? ' (more available)' : ''}
			</span>
		{/if}
	</div>

	<!-- Error -->
	{#if error}
		<div class="mb-4 rounded-md bg-red-50 p-4 font-mono text-sm text-red-700">{error}</div>
	{/if}

	<!-- Results -->
	{#if result && result.columns.length > 0}
		<div class="flex-1 overflow-auto rounded-lg border border-gray-200 bg-white shadow-sm">
			<table class="min-w-full divide-y divide-gray-200 text-sm">
				<thead class="sticky top-0 bg-gray-50">
					<tr>
						{#each result.columns as col}
							<th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 whitespace-nowrap">
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
	{/if}
</div>
