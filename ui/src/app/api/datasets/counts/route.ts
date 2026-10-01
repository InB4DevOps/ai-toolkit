import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { getDatasetsRoot } from '@/server/settings';
import { findMediaFilesRecursively } from '@/server/mediaFiles';

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

    // count media files per dataset (same rules as listImages: images + video +
    // audio each count as 1, _controls excluded). Only the count is returned, so
    // the payload stays tiny even for huge datasets.
    const counts: Record<string, number> = {};
    for (const name of folders) {
      const datasetFolder = path.resolve(datasetsPath, name);
      const mediaFiles = await findMediaFilesRecursively(datasetFolder);
      counts[name] = mediaFiles.length;
    }

    return NextResponse.json(counts);
  } catch (error) {
    console.error('Error counting dataset images:', error);
    return NextResponse.json({ error: 'Failed to fetch dataset counts' }, { status: 500 });
  }
}
