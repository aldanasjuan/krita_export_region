This plugin exports a desired region in the canvas and can optionally resize the export to a new size. 

Please fork for changes. I made this with chatgpt for personal use and I don't have time to do proper open source. I'll ignore issues or feature requests since I'm not a python developer.


## Install

Add the region_exporter folder to the resources folder, like your-resources-folder/pykrita/region_exporter

Add the region_exporter.desktop to the root of the pykrita folder. Should have a file like your-resources-folder/pykrita/region_exporter.desktop

Add the region_exporter.action to an 'actions' folder in the resources folder. Should have it like like your-resources-folder/actions/region_exporter.action

If you don't know what the your-resources-folder folder is, go to krita -> Settings -> Manage Resources -> Open Resource Folder


## Use

- Use ctrl+shift+e or go to Tools -> Scripts -> Export Region.
- Add the coordinates (x,y) and the rect size (width, height). 
- If you want to resize, select a New Width and New Height.
- Select a Rotation option. Same as rotating your image to the left or right. 
- If you select "Export Selected Layers" it will only export the selected layers, otherwise it exports the visible layers. Note: It doesn't support selecting a group, you must select the actual paint or vector layers you want. 
- Choose an output file and you're done.

## Regions

You can now save custom regions based of a selection.

- Select something
- Open the plugin
- Click "Grab Selection". This will update the x, y, width and height of the plugin. 
- Click "Save Region". 
- Name your region and confirm.
- Now you can select saved regions and reselect them using the "Select Region" button. 