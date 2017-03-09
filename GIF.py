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
            self.write('B',[ord(char)])

        ### Logical Screen Descriptor
        self.write('H',[Width])  # Canvas width
        self.write('H',[Height])  # Canvas Height

        self.write('B',[0b11110010]) 
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
        
        self.write('B',[0])  # Background Color Index*
        # *Index of color in the global color table (below) that non-assigned pixels take.
        self.write('B',[0])  # Pixel Aspect Ratio
        
        ### Global Color Table (GCT)
        for colorcode in GIF.GCT:
            for byte in colorcode:
                self.write('B',[byte])
        
        ### Application Extension, allows for animation
        self.write('B',[0x21])  # Extension Specifier:Shows that an extension follows
        self.write('B',[0xFF])  # Application Extension label
        
        app_identifier = 'NETSCAPE'
        app_auth_code = '2.0'
        app = app_identifier + app_auth_code
        self.write('B',[len(app)])  # Bytes that follow
        for char in app:
            self.write('B',[ord(char)])
        
        self.write('B',[3])  # Bytes that follow
        self.write('B',[1])  # Always 1
        self.write('H',[self.loops])  # Number of loops, 0 means no restriction.
        self.write('B',[0])  # Block terminator, 0 bytes follow
    
    def write(self, datatype, bytes_):
        '''
        B -> unsigned byte, H -> unsigned short.
        Full docs at https://docs.python.org/2/library/array.html
        '''
        array(datatype, [bytes_]).tofile(self.File)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.end_stream()
    
    def add_text(self, text, textleft=0, texttop=0, delay=0.1, color=1, bgcolor=0):
        '''
        Few decoders support this feature. 
        The images will often render but they will not display the text.
        '''
        self.write('B',[0x21])  # Extension Specifier: Shows that an extension follows
        self.write('B',[0x01])  # Plain Text Extension label
        self.write('B',[12])  # Block size
        self.write('H',[textleft])  # Text left position
        self.write('H',[texttop])  # Text right position
        self.write('H',[len(text)*8])  # Image Grid Width
        self.write('H',[8])  # Image Grid Height
        self.write('B',[8])  # Character Cell Width
        self.write('B',[8])  # Character Cell Height
        self.write('H',[color])  # Font color
        self.write('H',[bgcolor])  # Background color
        
        self.write('B',[0x21])  # Extension Specifier: Shows that an extension follows
        maxbyteFlow = 255
        for i, char in enumerate(text):
            if i % maxbyteFlow == 0:
                # Bytes that follow
                self.write('B',[len(char[i:i+maxbyteFlow])])
            self.write('B',[ord(char)])  # Extension Specifier: Shows that an extension follows
        self.write('H',[0])  # Extension Specifier: Shows that an extension follows
        
    
    def add_image(self,canvasobj, imgleft=0, imgtop=0, delay=0.1, overlap=True):        
        ### Graphics Control Extension
        self.write('B',[0x21])  # Extension Specifier: Shows that an extension follows
        self.write('B',[0xF9])  # Graphics Control Extension label
        self.write('B',[4])  # Block size: Number of bytes that follow
        self.write('B',[2**(3-overlap)])  # Packed field. Disposal method is set to 1; overlapping
        self.write('H',[int(delay*100)])  # Delay time (in 1/100 seconds)
        self.write('B',[0])  # Transparent Color Index*
        # *pixel with this index will appear transparent; background color will show instead.
        self.write('B',[0])  # Block terminator, 0 bytes follow

        ### Image descriptor
        self.write('B',[0x2C])  # Image separator (comma)
        self.write('H',[imgleft])  # Image Left position
        self.write('H',[imgtop])  # Image Top position
        self.write('H',[canvasobj.Width])  # Image Width
        self.write('H',[canvasobj.Height])  # Image Height
        self.write('B',[0])  # Packed Field, all subvalues currently set to 0
        
        ### Image data
        self.write('B',[3])  # LZW min code size = GCT size+1
        index_stream = canvasobj.get_index_stream()
        print('Compressing...')
        compressed = LZW_compress(index_stream)
        print('Compression finished.')
        maxbyteFlow = 255  # A single byte is dedicated to the # of bytes that follow, max value is 255
        for i,byte in enumerate(compressed):
            if i % maxbyteFlow == 0:
                # Bytes that follow
                self.write('B',[len(compressed[i:i+maxbyteFlow])])
            self.write('B',[byte])
        self.write('B',[0])  # Block terminator, 0 bytes follow
    
    def end_stream(self):
        self.write('B',[0x3B])
        self.File.close()
            
if __name__ == '__main__':
    with GIF('Texttesting.gif',500,500) as gif:
        import Render
        bild = Render.Canvas(500,500)
        bild.add_graphics(Render.Line(0,0,490,490))
        gif.add_image(bild)
        bild.add_graphics(Render.Line(490,0,0,490))
        gif.add_image(bild)