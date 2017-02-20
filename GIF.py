# coding: iso-8859-15

# 2016-09-03
# Axel Engström, Sci14

'''
Source used to compose the file structure:
https://www.w3.org/Graphics/GIF/spec-gif89a.txt
'''


from array import array
from LZW import LZW_compress, code_to_bin

class GIF:
    #Global Color Table:
    #       White         Black   Red        Green      Blue      Yellow      Magenta     Cyan
    GCT = [(255,255,255),(0,0,0),(243,16,0),(18,206,8),(0,0,255),(255,255,0),(255,0,255),(0,255,255)]

    def __init__(self, filename, Width, Height, loops=0):
        print('Initialising GIF...')
        
        if '.gif' not in filename.lower():
            filename += '.gif'
        self.File = open(filename,'wb')
        self.Width = Width
        self.Height = Height
        self.loops = loops if 0 <= loops < 2**16 else 0
        
        #Note: B -> unsigned byte, H -> unsigned short
        
        ### Header
        for char in 'GIF89a':
            array('B',[ord(char)]).tofile(self.File)

        ### Logical Screen Descriptor
        array('H',[Width]).tofile(self.File)  # Canvas width
        array('H',[Height]).tofile(self.File)  # Canvas Height

        array('B',[0b11110010]).tofile(self.File) 
        ''' Packed field: 1  111  0  010
                          |  |    |  |_
                          |  |    |_   Size of GCT*
                          |  |_     Sort Flag*
                          |_   Color Resolution*
                            Global Color Table (GCT) Flag*

        *1 if a GCT exists.
        *Bits per pixel.
        *1 if colors in GCT are to be sorted in decreasing frequency, may help decoder.
        *Amount of colors in color table is 2^(n+1).
        '''
        
        array('B',[0]).tofile(self.File)  # Background Color Index*
        # *Index of color in the global color table (below) that non-assigned pixels take.
        array('B',[0]).tofile(self.File)  # Pixel Aspect Ratio
        
        ### Global Color Table (GCT)
        for colorcode in GIF.GCT:
            for byte in colorcode:
                array('B',[byte]).tofile(self.File)
        
        ### Application Extension, allows for animation
        array('B',[0x21]).tofile(self.File)  # Extension Specifier:Shows that an extension follows
        array('B',[0xFF]).tofile(self.File)  # Application Extension label
        
        app_identifier = 'NETSCAPE'
        app_auth_code = '2.0'
        app = app_identifier + app_auth_code
        array('B',[len(app)]).tofile(self.File)  # Bytes that follow
        for char in app:
            array('B',[ord(char)]).tofile(self.File)
        
        array('B',[3]).tofile(self.File)  # Bytes that follow
        array('B',[1]).tofile(self.File)  # Always 1
        array('H',[self.loops]).tofile(self.File)  # Number of loops, 0 means no restriction.
        array('B',[0]).tofile(self.File)  # Block terminator, 0 bytes follow
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.end_stream()
    
    def add_text(self, text, textleft=0, texttop=0, delay=0.1, color=1, bgcolor=0):
        '''
        Few decoders support this feature. 
        The images will often render but they will not display the text.
        '''
        array('B',[0x21]).tofile(self.File)  # Extension Specifier: Shows that an extension follows
        array('B',[0x01]).tofile(self.File)  # Plain Text Extension label
        array('B',[12]).tofile(self.File)  # Block size
        array('H',[textleft]).tofile(self.File)  # Text left position
        array('H',[texttop]).tofile(self.File)  # Text right position
        array('H',[len(text)*8]).tofile(self.File)  # Image Grid Width
        array('H',[8]).tofile(self.File)  # Image Grid Height
        array('B',[8]).tofile(self.File)  # Character Cell Width
        array('B',[8]).tofile(self.File)  # Character Cell Height
        array('H',[color]).tofile(self.File)  # Font color
        array('H',[bgcolor]).tofile(self.File)  # Background color
        
        array('B',[0x21]).tofile(self.File)  # Extension Specifier: Shows that an extension follows
        maxbyteFlow = 255
        for i, char in enumerate(text):
            if i % maxbyteFlow == 0:
                # Bytes that follow
                array('B',[len(char[i:i+maxbyteFlow])]).tofile(self.File)
            array('B',[ord(char)]).tofile(self.File)  # Extension Specifier: Shows that an extension follows
        array('H',[0]).tofile(self.File)  # Extension Specifier: Shows that an extension follows
        
    
    def add_image(self,canvasobj, imgleft=0, imgtop=0, delay=0.1, overlap=True):        
        ### Graphics Control Extension
        array('B',[0x21]).tofile(self.File)  # Extension Specifier: Shows that an extension follows
        array('B',[0xF9]).tofile(self.File)  # Graphics Control Extension label
        array('B',[4]).tofile(self.File)  # Block size: Number of bytes that follow
        array('B',[2**(3-overlap)]).tofile(self.File)  # Packed field. Disposal method is set to 1; overlapping
        array('H',[int(delay*100)]).tofile(self.File)  # Delay time (in 1/100 seconds)
        array('B',[0]).tofile(self.File)  # Transparent Color Index*
        # *pixel with this index will appear transparent; background color will show instead.
        array('B',[0]).tofile(self.File)  # Block terminator, 0 bytes follow

        ### Image descriptor
        array('B',[0x2C]).tofile(self.File)  # Image separator (comma)
        array('H',[imgleft]).tofile(self.File)  # Image Left position
        array('H',[imgtop]).tofile(self.File)  # Image Top position
        array('H',[canvasobj.Width]).tofile(self.File)  # Image Width
        array('H',[canvasobj.Height]).tofile(self.File)  # Image Height
        array('B',[0]).tofile(self.File)  # Packed Field, all subvalues currently set to 0
        
        ### Image data
        array('B',[3]).tofile(self.File)  # LZW min code size = GCT size+1
        index_stream = canvasobj.get_index_stream()
        print('Compressing...')
        compressed = LZW_compress(index_stream)
        print('Compression finished.')
        maxbyteFlow = 255  # A single byte is dedicated to the # of bytes that follow, max value is 255
        for i,byte in enumerate(compressed):
            if i % maxbyteFlow == 0:
                # Bytes that follow
                array('B',[len(compressed[i:i+maxbyteFlow])]).tofile(self.File)
            array('B',[byte]).tofile(self.File)
        array('B',[0]).tofile(self.File)  # Block terminator, 0 bytes follow
    
    def end_stream(self):
        array('B',[0x3B]).tofile(self.File)
        self.File.close()
            
if __name__ == '__main__':
    with GIF('Texttesting.gif',500,500) as gif:
        import Render
        bild = Render.Canvas(500,500)
        bild.add_graphics(Render.Line(0,0,490,490))
        gif.add_image(bild)
        bild.add_graphics(Render.Line(490,0,0,490))
        gif.add_image(bild)