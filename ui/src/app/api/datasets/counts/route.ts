import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { getDatasetsRoot } from '@/server/settings';
import {
  audioExtensions,
  findMediaFilesRecursively,
  imageExtensions,
  type MediaCounts,
  videoExtensions,
} from '@/server/mediaFiles';

export async function GET() {
  try {
    const datasetsPath = await getDatasetsRoot();

    // if folder doesnt exist, create it
    try {
      await fs.promises.access(datasetsPath);
    } catch {
      await fs.promises.mkdir(datasetsPath);
    }

    // find all the folders in the datasets folder
    const folders = (await fs.promises.readdir(datasetsPath, { withFileTypes: true }))
      .filter(dirent => dirent.isDirectory())
      .filter(dirent => !dirent.name.startsWith('.'))
      .map(dirent => dirent.name);

    const counts: Record<string, MediaCounts> = {};
    for (const name of folders) {
      const datasetFolder = path.resolve(datasetsPath, name);
      try {
        const mediaFiles = await findMediaFilesRecursively(datasetFolder);
        const datasetCounts: MediaCounts = { image: 0, video: 0, audio: 0 };
        for (const mediaPath of mediaFiles) {
          const ext = path.extname(mediaPath).toLowerCase();
          if (imageExtensions.includes(ext)) datasetCounts.image += 1;
          else if (videoExtensions.includes(ext)) datasetCounts.video += 1;
          else if (audioExtensions.includes(ext)) datasetCounts.audio += 1;
        }
        counts[name] = datasetCounts;
      } catch (error) {
        console.error(`Error counting media in dataset '${name}':`, error);
      }
    }

    return NextResponse.json(counts);
  } catch (error) {
    console.error('Error counting dataset media:', error);
    return NextResponse.json({ error: 'Failed to fetch dataset counts' }, { status: 500 });
  }
}
