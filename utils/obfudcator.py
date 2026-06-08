import os
import uuid
import shutil
import asyncio
import shlex
import config

class Obfuscator:
    def __init__(self, file_path: str, options=None):
        self.file_path = file_path
        if isinstance(options, (list, tuple)):
            options = {'flags': options}
        self.options = options or {}
        method = self.options.get('method', 'pyarmor')
        self.file_name = self.options.get('file_name', 'protected_code.zip')
        # normalize method string: accept 'python-obfuscator' or 'python_obfuscator'
        self.method = str(method).lower().replace('-', '_')
        self.task_id = self.file_name.split('.')[0] + '_' + str(uuid.uuid4())
        self.user_work_dir = os.path.join(config.UPLOAD_FOLDER, self.task_id)
        self.extract_dir = os.path.join(self.user_work_dir, "source_code")
        # place les résultats obfusqués dans le dossier `dist` du répertoire de travail courant
        # avec un sous-dossier par tâche pour éviter les collisions
        self.dist_dir = os.path.join(os.getcwd(), "dist", self.task_id)

    async def _obfuscate_with_pyarmor(self):
        # Commande : pyarmor gen -r -O <dossier_sortie> <dossier_source>
        cmd = f"pyarmor gen -r -O {self.dist_dir} {self.source_dir}"
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            # Nettoyage en cas d'erreur
            shutil.rmtree(self.user_work_dir, ignore_errors=True)
            err = stderr.decode().strip() or "PyArmor failed"
            raise RuntimeError(err)

    async def _obfuscate_with_python_obfuscator(self):
        # Écrire les fichiers obfusqués directement dans le dossier de travail `dist/<task_id>`
        obfuscate_dir = self.dist_dir

        path_to_obfuscated_files = []

        for root, dirs, files in os.walk(self.copy_dir):
            for file in files:
                src_path = os.path.join(root, file)

                if not file.endswith(".py"):
                    # Laisser les fichiers non-Python tels quels (ils sont déjà copiés dans self.copy_dir)
                    continue

                if await self._detected_if_ignore_obfuscation(src_path):
                    continue

                # if file.startswith("__init__"):
                #     continue

                # if file == "module.py":
                #     continue

                # Exécuter pyobfuscate et capturer la sortie sur stdout
                cmd = f"pyobfuscate -i {shlex.quote(src_path)} --stdout"
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    shutil.rmtree(self.user_work_dir, ignore_errors=True)
                    err = stderr.decode().strip() or "python-obfuscator failed"
                    raise RuntimeError(err)

                # Écrire le résultat obfusqué en remplacement du fichier source copié
                with open(src_path, "wb") as f:
                    f.write(stdout)

    async def _detected_if_ignore_obfuscation(self, file_path: str):
        """Lit le fichier de manière non-bloquante pour chercher le tag d'ignorance."""
        loop = asyncio.get_running_loop()
        
        def _check():
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    # On lit uniquement la première ou les deux premières lignes pour la performance
                    first_lines = "".join([f.readline() for _ in range(3)])
                    return "# ignore-obfuscation" in first_lines
            except Exception:
                return False

        return await loop.run_in_executor(None, _check)

    async def _copy_source_code(self):
        file_name_without_ext = self.file_name.rsplit('.', 1)[0]
        source_dir = os.path.join(self.extract_dir, file_name_without_ext)
        copy_dir = os.path.join(self.dist_dir, file_name_without_ext)
        # copie le dossier source dans un dossier dist
        shutil.copytree(source_dir, copy_dir)

        self.source_dir = source_dir
        self.copy_dir = copy_dir

    async def obfuscate(self):
        # 2. Créer un identifiant unique pour cette session
        os.makedirs(self.user_work_dir, exist_ok=True)
        # Ensure task-level dist directory exists (parent for copytree)
        os.makedirs(self.dist_dir, exist_ok=True)

        # 3. Extraire le ZIP de manière asynchrone (via run_in_executor pour ne pas bloquer)
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, shutil.unpack_archive, self.file_path, self.extract_dir)
        except Exception as e:
            shutil.rmtree(self.user_work_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to extract archive: {e}")

        await self._copy_source_code()

        if self.method == 'pyarmor':
            await self._obfuscate_with_pyarmor()
        elif self.method == 'python_obfuscator':
            await self._obfuscate_with_python_obfuscator()
        else:
            # unknown method
            shutil.rmtree(self.user_work_dir, ignore_errors=True)
            raise ValueError(f"Invalid obfuscation method: {self.method}")

        # 5. Compresser le résultat (le dossier dist contenant le runtime et le code obfusqué)
        result_zip_base = os.path.join(config.OUTPUT_FOLDER, f"{self.task_id}")
        await loop.run_in_executor(None, shutil.make_archive, result_zip_base, 'zip', self.dist_dir)
        final_zip_path = f"{result_zip_base}.zip"

        # 6. Nettoyer les fichiers sources d'origine (Sécurité/Confidentialité)
        shutil.rmtree(self.user_work_dir, ignore_errors=True)

        return final_zip_path