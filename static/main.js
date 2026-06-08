document.addEventListener('DOMContentLoaded', () => {
	const form = document.getElementById('obfuscate-form');
	const resultText = document.getElementById('result-text');
	const downloadLink = document.getElementById('download-link');
	const historyBody = document.getElementById('history-table-body');
	const clearBtn = document.getElementById('clear-history');

	loadHistory();

	form.addEventListener('submit', async (e) => {
		e.preventDefault();

		const fileInput = form.querySelector('input[type="file"]');
		if (!fileInput || !fileInput.files || !fileInput.files.length) {
			resultText.textContent = 'Veuillez sélectionner un fichier ZIP.';
			return;
		}

		const formData = new FormData(form);
		setLoading(true);
		resultText.textContent = '';
		downloadLink.style.display = 'none';

		try {
			const resp = await fetch('/obfuscate', { method: 'POST', body: formData });
			const data = await resp.json();
			if (!resp.ok) {
				throw new Error(data.error || 'Erreur lors de l\'obfuscation');
			}

			const filePath = data.file_path;
			const obfuscatedName = basename(filePath);
			const downloadUrl = `/download?file_path=${encodeURIComponent(filePath)}`;

			resultText.textContent = `Obfuscation terminée — ${obfuscatedName}`;
			downloadLink.href = downloadUrl;
			downloadLink.style.display = 'inline-block';

			// try fetching sha256 (optional)
			try {
				const shaResp = await fetch(`/sha256?file_path=${encodeURIComponent(filePath)}`);
				if (shaResp.ok) {
					const shaData = await shaResp.json();
					resultText.textContent += ` — SHA256: ${shaData.sha256}`;
				}
			} catch (_) {}

			addHistoryEntry({ original: fileInput.files[0].name, obfuscated: obfuscatedName, timestamp: new Date().toLocaleString(), download: downloadUrl });

		} catch (err) {
			resultText.textContent = 'Erreur: ' + (err.message || err);
		} finally {
			setLoading(false);
		}
	});

	clearBtn && clearBtn.addEventListener('click', () => {
		localStorage.removeItem('melodi_history');
		while (historyBody.firstChild) historyBody.removeChild(historyBody.firstChild);
	});

	function addHistoryEntry(entry) {
		const id = Date.now();
		const tr = document.createElement('tr');
		tr.innerHTML = `<td>${id}</td><td>${escapeHtml(entry.original)}</td><td><a href="${entry.download}">${escapeHtml(entry.obfuscated)}</a></td><td>${entry.timestamp}</td>`;
		historyBody.prepend(tr);

		const history = JSON.parse(localStorage.getItem('melodi_history') || '[]');
		history.unshift({ id, ...entry });
		localStorage.setItem('melodi_history', JSON.stringify(history));
	}

	function loadHistory() {
		const history = JSON.parse(localStorage.getItem('melodi_history') || '[]');
		history.forEach(item => {
			const tr = document.createElement('tr');
			tr.innerHTML = `<td>${item.id}</td><td>${escapeHtml(item.original)}</td><td><a href="${item.download}">${escapeHtml(item.obfuscated)}</a></td><td>${item.timestamp}</td>`;
			historyBody.appendChild(tr);
		});
	}

	function setLoading(isLoading) {
		const btn = form.querySelector('input[type="submit"]');
		if (!btn) return;
		btn.disabled = isLoading;
		btn.value = isLoading ? 'Obfuscating...' : 'Obfuscate';
	}

	function basename(path) {
		return path.split('/').pop();
	}

	function escapeHtml(unsafe) {
		return String(unsafe).replace(/[&<>\"']/g, function (m) {
			return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]);
		});
	}
});
