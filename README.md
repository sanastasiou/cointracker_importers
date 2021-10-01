# cointracker_importers
Various importers for cointracker

## To convert nexo .csv format to cointracker .csv format:

- Download nexo csv file.
- run python NexoToCointrackerConverter.py --nexo <nexo.csv>

You should now have a cointracker compatible .csv file sorted by date. Interest transactions are marked as "staked" since cointracker doesn't support "interest" tag.
