import random
from fontTools.ttLib import TTFont, TTLibError
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.basePen import BasePen
import pathops
import os

class JitterPen(BasePen):
    """Intercepts vector drawing commands and aggressively randomizes

    the coordinate positions to create jagged, glitchy edges.
    """
    def __init__(self, glyph_set, target_pen, jitter_range=(-80, 80)):
        super().__init__(glyph_set)
        self.target_pen = target_pen
        self.min_j, self.max_j = jitter_range

    def _jitter(self, pt):
        # pt[0] is X coordinate, pt[1] is Y coordinate
        return (pt[0] + random.randint(self.min_j, self.max_j), 
                pt[1] + random.randint(self.min_j, self.max_j))

    def _moveTo(self, pt):
        self.target_pen.moveTo(self._jitter(pt))

    def _lineTo(self, pt):
        self.target_pen.lineTo(self._jitter(pt))

    def _curveToOne(self, pt1, pt2, pt3):
        self.target_pen.curveTo(self._jitter(pt1), self._jitter(pt2), self._jitter(pt3))

    def _qCurveToOne(self, pt1, pt2):
        self.target_pen.qCurveTo(self._jitter(pt1), self._jitter(pt2))

    def _closePath(self):
        self.target_pen.closePath()

    def _endPath(self):
        self.target_pen.endPath()


def build_layered_monstrosity(font_paths, output_font_name, jitter_intensity=70):
    output_ttf_path = '.\\' + output_font_name + '.ttf'
    print("Loading source fonts...")
    # Skip source fonts whose tables cannot be parsed.
    fonts = []
    glyph_sets = []
    for font_path in font_paths:
        font = None
        try:
            font = TTFont(font_path)
            glyph_set = font.getGlyphSet()
        except (OSError, TTLibError) as error:
            print(f"Skipping invalid font '{font_path}': {error}")
            if font is not None:
                font.close()
            continue
        fonts.append(font)
        glyph_sets.append(glyph_set)

    if not fonts:
        raise ValueError("No valid source fonts were found.")
    
    # Rewritten outlines cannot retain variable-font glyph deltas.
    base_font: TTFont = next(
        (font for font in fonts if "fvar" not in font and "gvar" not in font),
        None,
    )
    if base_font is None:
        raise ValueError("At least one static TrueType font is required as the output base.")
    
    name_table = base_font['name']
    postscript_name = ''.join(
        char for char in output_font_name
        if char.isascii() and (char.isalnum() or char in '-_')
    ) or 'Untitled'
    for name_id, value in (
        (1, output_font_name),
        (4, output_font_name),
        (6, postscript_name),
    ):
        name_table.setName(value, name_id, 3, 1, 0x409)

    base_glyf = base_font['glyf']
    base_glyph_set = base_font.getGlyphSet()
    
    print("Layering, jittering, and piercing holes...")
    for glyph_name in base_font.getGlyphOrder():
        # Initialize a single canvas path for this character slot
        combined_path = pathops.Path()
        pathops_pen = pathops.PathPen(combined_path)
        
        has_geometry = False
        
        # 1. Look into every font layer for this specific character slot
        for g_set in glyph_sets:
            if glyph_name in g_set:
                # Intercept vectors through our JitterPen to scatter points
                jitter_pen = JitterPen(
                    g_set, 
                    pathops_pen, 
                    jitter_range=(-jitter_intensity, jitter_intensity)
                )
                try:
                    g_set[glyph_name].draw(jitter_pen)
                    has_geometry = True
                except Exception:
                    # Skip sub-layers if their glyph records are corrupt/empty
                    continue
        
        if not has_geometry:
            continue
            
        # 2. Force Skia-Pathops to collapse the overlapping layers.
        # It calculates all line intersections across the layered noise,
        # treating overlapping vector zones as inverse cutouts/holes.
        try:
            simplified_path = pathops.simplify(combined_path)
        except pathops.PathOpsError:
            continue

        # 3. Compile the resulting chaotic vector framework back to TrueType
        tt_pen = TTGlyphPen(base_glyph_set)
        simplified_path.draw(tt_pen)
        
        # Update the base font's glyf table with our final unreadable mesh
        if glyph_name in base_glyf.glyphs:
            base_glyf[glyph_name] = tt_pen.glyph()

    print(f"Saving completed unreadable monstrosity to: {output_ttf_path}")
    base_font.save(output_ttf_path)


if __name__ == "__main__":
    # Define your source input fonts here
    os.listdir("./input_fonts")  # Ensure the input fonts directory exists and contains .ttf files
    input_fonts = [os.path.join("input_fonts", f) for f in os.listdir("input_fonts") if f.endswith(".ttf")]
    
    output_name = input('Enter a name for your font (or leave blank for "Fuck Script"): ').strip()
    if not output_name:
        output_name = "Fuck Script"
    
    # Tweak intensity: 40 = mild overlap shredding | 90+ = extreme chaotic distortion
    build_layered_monstrosity(input_fonts, output_name, jitter_intensity=int(input('Enter jitter intensity (<40: mild jittering, 90+: real fontfuck experience): ').strip()))
