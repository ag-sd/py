# Imageplay - A windowed image slide-show app and basic image editor
Imageplay lets you run a slide-show of a collection of images. The slide-show runs in windowed mode

### Features
* Drag and drop images to start a slide-show

### TO-DO
- [x] Drag and drop images to start a slide-show
- [x] Choose a folder as image source
- [x] Play GIF images frame-by-frame
- [x] Play in Order / Random. 
- [x] Loop / Stop at end of list
- [x] Crop images
- [ ] Resize images
- [ ] Rotate images
- [ ] Color images
- [x] Display image properties
- [ ] Duplicate Image Finder // TODO-Flesh out
- [ ] Library Tools
- [ ] Save an image playlist
- [ ] Filter images by dimension, color etc.
- [x] Unit Tests
- [x] Playlist to use a stack
- [ ] Fine tuned zoom in and zoom out

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

**Wed Mar 20 23:50:00 EDT 2019**
- Duplicate Image Finder Multi-Threaded performance optimisations
- Improved image display grid for duplicate images
- Improved metadata preview for duplicate images

**Wed Mar 13 00:09:29 EDT 2019**
- Added basic duplicate image finder framework
- Additional widgets to support duplicate image dialog

**Wed Mar  6 21:31:47 EST 2019**
- Added zoom in and zoom out
- Image Properties widget added
- Image Cropping added
- General code refactoring and separation of actions

**Sun Feb 24 00:48:37 EST 2019**
- Added command line support
- Added scaling support
 
**Thu Feb 21 21:31:15 EST 2019**
- Improved UX with play controls
- Updated playlist to internally use a stack with infinite history
- Added image change and animation change settings
- Added directory support
   
**Wed Feb 13 20:29:03 EST 2019**  
Updates and ability to play GIF images added 

**Wed Feb  6 23:55:27 EST 2019**  
Initial commit of the code  