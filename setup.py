from distutils.core import setup

#This is a list of files to install, and where
#(relative to the 'root' dir, where setup.py is)
#You could be more specific.
files = ["annelia/*"]

setup(name = "Annelia",
    version = "0.0.1",
    description = "Static file http edge server.",
    author = "Stephane Jolicoeur-Fidelia",
    author_email = "s.jolicoeur@gmail.com",
    url = "http://annelia.stephanejolicoeur.com/",
    #Name the folder where your packages live:
    #(If you have other packages (dirs) or modules (py files) then
    #put them into the package directory - they will be found 
    #recursively.)
    packages = ['annelia'],
    #'package' package must contain files (see list above)
    #I called the package 'package' thus cleverly confusing the whole issue...
    #This dict maps the package name =to=> directories
    #It says, package *needs* these files.
    package_data = {'package' : files },
    #'runner' is in the root.
    scripts = ["runner", "annelia/annelia.py"],
    long_description = """In short this replicates the abilities of an edge server, demand content if it's not on the server it will ask it's configured friendly servers if they have the file and if so will download it from them.""",
    #
    #This next part it for the Cheese Shop, look a little down the page.
    #classifiers = []     
    #requires = 
    install_requires=[
        'CherryPy>=3.2.0'
    ]
) 
