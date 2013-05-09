# sublime-less2css

Sublime Text 2 Plugin to compile less files to css on save
Requires lessc installed on PATH

# Features


 * Automatically compile less -> css on save when editing a .less file in sublime
 * Reports compilation errors
 * Compile all less files in a directory to css files

NB This plugin requires lessc to be in your execution path

# Installation

## Install The Plugin

Either clone into your sublime packages directory, or just use [Package Control](https://github.com/wbond/sublime_package_control/)

## Install Requirements

Less2Css requires lessc to compile less to css.

### Mac OS X / Linux(Ubuntu/Debian…)

1. Install [NodeJS](http://nodejs.org) (you may need nodejs-legacy - see [issue #23](https://github.com/timdouglas/sublime-less2css/issues/23))
2. Install npm([NodeJS Package Manager](https://npmjs.org/doc/README.html))
3. Install less

##
    npm install less -gd


### Windows

1. Clone [less.js-windows](https://github.com/duncansmart/less.js-windows)
2. Add the path of your less.js-windows to PATH environment variable([How to?](http://msdn.microsoft.com/en-us/library/ee537574.aspx)).

[中文版详细安装教程](http://fdream.net/blog/article/783.aspx)

# Configuration
## autoCompile
The allowed values are *true* and *false*. When this setting is set to *true* the plugin will compile your LESS file each time you save it.

## lessBaseDir
## lesscCommand
This setting can be used to specify a different compiler. When it is left empty the default compiler, named *lessc*, will be used.

## main_file
When you specify a main file only this file will get compiled when you save any LESS file. This is especially useful if you have one LESS file which imports all your other LESS files. Please note that this setting is only used when compiling a single LESS file and not when compiling all LESS files in the LESS base folder through *Project \ Less>Css \ Compile all less in less base directory to css*.

## minify
The allowed values are *true* and *false*. When this setting is set to *true* the LESS compiler will be instructed to create a minified CSS file.

## outputDir
## outputFile
When you specify an output file, this will be the file name used to compile **any** LESS file to. When you build all LESS file in the LESS base folder through *Project \ Less>Css \ Compile all less in less base directory to css* you will only have the CSS of the last compiled file!

## showErrorWithWindow