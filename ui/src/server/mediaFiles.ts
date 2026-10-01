import fs from 'fs';
import path from 'path';

/**
 * Recursively finds all media files (images, video, audio) in a directory and its subdirectories
 * @param dir Directory to search
 * @returns Array of absolute paths to media files
 */
export async function findMediaFilesRecursively(dir: string): Promise<string[]> {
  const imageExtensions = ['.png', '.jpg', '.jpeg', '.webp', '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.m4v', '.flv', '.mp3', '.wav', '.flac', '.ogg'];
  let results: string[] = [];

  // withFileTypes avoids a separate stat per entry — a big win on large datasets.
  // Async readdir yields between directories so other requests aren't blocked.
  const entries = await fs.promises.readdir(dir, { withFileTypes: true });

  const subdirs: string[] = [];
  for (const entry of entries) {
    const name = entry.name;
    if (name.startsWith('.')) continue;
    const itemPath = path.join(dir, name);

    if (entry.isDirectory()) {
      if (name === '_controls') continue;
      subdirs.push(itemPath);
    } else if (entry.isFile()) {
      const ext = path.extname(name).toLowerCase();
      if (imageExtensions.includes(ext)) {
        results.push(itemPath);
      }
    }
  }

  // Recurse into subdirectories concurrently.
  const nested = await Promise.all(subdirs.map(subdir => findMediaFilesRecursively(subdir)));
  for (const list of nested) {
    results = results.concat(list);
  }

  return results;
}
