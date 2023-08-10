
###Duplicate Finder TODO
- [ ] Add an option to have a reference Database to compare new files only
- [ ] Add a report with the number of files to be deleted by directory
- [ ] Add an ergonomic tool to confirm Auto-Selections, actions applies only on confirmed pictures
- [ ] Display the larger images side by side for comparison
- [ ] Improve the internal database's index algorythm to increase speed
- [ ] Improve the auto-select options
- [ ] Improve the comparison engine's memory managment to increase speed
- [ ] Fix and improve the thumbnails display engine (including Thumbsize, and a label/filesize/resolution)
- [ ] Fix and improve the projects engine 
- [ ] Add a count of the number of pictures being deleted/moved in the dialog
- [ ] Add a small display on the thumbnail: format, resolution and size
- [ ] Add which program is used to open a container### Changelog
- [ ] Fix groups shouldn't disapear if only one image remains after a move

mogrify -auto-level -colorspace Gray -resize 50x50! -path y/ *.jpg

mogrify -auto-level -resize 50x50! -path y/ *histogram.jpg

magick 20230406_082110.jpg  -define histogram:unique-colors=false histogram:20230406_082110_histogram.jpg

Create Fingerprint
mogrify -auto-level -colorspace Gray -resize 50x50! -path y/ *.jpg
Create Histogram
magick 20230406_082110.jpg  -define histogram:unique-colors=false histogram:20230406_082110_histogram.jpg
mogrify -auto-level -resize 50x50! -path y/ *histogram.jpg
Generate Fingerprint StringMap
Generate Histogram StringMap
Levenshtein Distance between the 2