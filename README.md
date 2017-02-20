#SimpleGif
Create simple GIF animations in python using lines, circles, functions, polygons and points.

##Requirements
None at the moment! I am however looking into optimising the LZW compression with numpy.

##Code Examples
The baseline program to draw a line:

```python
import Render
from GIF import GIF

WIDTH, HEIGHT = 500, 500
with GIF('BaseLine.gif', WIDTH, HEIGHT) as gif:  # Creates file called BaseLine.gif
    ### Initialise a frame
    frame = Render.Canvas(WIDTH, HEIGHT) # Blank white canvas
    
    ### Add desired graphics
    frame.add_graphics(Render.Line(100,350,200,400))
    #...
    
    ### Add the frame
    gif.add_image(frame, delay=0.1) # add several frames to create an animation
```
This is all usually done inside a loop that gradually changes the state of a system.

##Results
Visualising algorithms

![SierpinskyNodes](doc/Sierpinsky_nodes.gif)

Or animating physical simulations

![LargerBuoyancy](doc/LargerBuoyancy.gif)

![ChargedParticles](doc/ChargedParticles.gif)