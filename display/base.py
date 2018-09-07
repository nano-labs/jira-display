from datetime import timedelta
from PIL import Image, ImageDraw, ImageFont

DEFAULT_FONT = ImageFont.truetype("display/default.ttf", 16)
CLOCK_FONT = ImageFont.truetype("display/digital.ttf", 35)
SMALL_DEFAULT_FONT = ImageFont.truetype("display/digital.ttf", 13)
MEDIUM_DEFAULT_FONT = ImageFont.truetype("display/digital.ttf", 23)

def image_to_hex(image):
    data = image.getdata()
    output = []
    bit_position = 0
    binary = ''
    for pixel in data:
        bit_position += 1
        binary += str(int(pixel > 0))
        if bit_position == 8:
            output.append(hex(int(binary, 2)))
            bit_position = 0
            binary = ''
    return output

def image_to_bin(image):
    data = image.getdata()
    output = []
    row = []
    column_position = 0
    bit_position = 0
    binary = 'B'
    for pixel in data:
        bit_position += 1
        binary += str(int(pixel > 0))
        if bit_position == 8:
            row.append(binary)
            bit_position = 0
            binary = 'B'
            column_position += 1
        if column_position >= (image.size[0] / 8):
            output.append(row)
            row = []
            column_position = 0
    return output

def image_to_bin(image):
    data = image.getdata()
    output = []
    row = []
    column_position = 0
    bit_position = 0
    binary = ''
    for pixel in data:
        bit_position += 1
        binary += str(int(pixel > 0))
        if bit_position == image.size[0]:
            print(binary.replace("0", " ").replace("1", "#"))
            bit_position = 0
            binary = ''



class BaseDisplay:

    size = (128, 32)

    def __init__(self, inversed_colors=False):
        self.image = Image.new('1', self.size, (int(inversed_colors),))
        self.d = ImageDraw.Draw(self.image)

    def save(self, filename):
        self.image.save(filename)


class DisplayText(BaseDisplay):

    def __init__(self, text, inversed_colors=False):
        super().__init__(inversed_colors)
        lines = ["", ""]
        for i in range(len(text)):
            x, y = DEFAULT_FONT.getsize(text[:i])
            if x > 2 * self.size[0]:
                break
            elif x < self.size[0] - 10:
                lines[0] += text[i]
            elif x < 2 * self.size[0]:
                lines[1] += text[i]

        # Line 1
        self.d.text(
            (
                0,  # X start position
                0  # Y start position
            ),
            lines[0],  # Text
            fill=(int(not inversed_colors),),  # color
            font=DEFAULT_FONT
        )
        # Line 2
        self.d.text(
            (
                0,  # X start position
                self.size[1] - DEFAULT_FONT.getsize(lines[1])[1] - 1
            ),
            lines[1],
            fill=(int(not inversed_colors),),  # color
            font=DEFAULT_FONT
        )


class DisplayIssue(BaseDisplay):

    def __init__(self, issue, status, clock=None, inversed_colors=False):
        super().__init__(inversed_colors)

        project_key, issue_code = issue.key.lower().split("-")
        if not clock:
            spent = issue.fields.timespent or 0
            if spent >= 60 * 60:  # one hour
                spent = int(spent / 60)  # this variable become minutes
            clock = "{:02d}:{:02d}".format(int(spent / 60), int(spent % 60))

        status_size = SMALL_DEFAULT_FONT.getsize(status)
        project_key_size = SMALL_DEFAULT_FONT.getsize(project_key)
        issue_code_size = MEDIUM_DEFAULT_FONT.getsize(issue_code)
        clock_size = CLOCK_FONT.getsize(clock)

        # status
        self.d.text(
            (
                5,  # X start position
                1  # Y start position
            ),
            status,  # Text
            fill=(int(not inversed_colors),),  # color
            font=SMALL_DEFAULT_FONT
        )
        # project key
        self.d.text(
            (
                5,  # X start position
                self.size[1] - project_key_size[1] - 1  # Y start position
            ),
            project_key,  # Text
            fill=(int(not inversed_colors),),  # color
            font=SMALL_DEFAULT_FONT
        )
        # issue code
        self.d.text(
            (
                5 + project_key_size[0],
                self.size[1] - issue_code_size[1] - 1
            ),
            issue_code, fill=(int(not inversed_colors),),
            font=MEDIUM_DEFAULT_FONT
        )
        # clock
        self.d.text(
            (
                self.size[0] - clock_size[0] - 1,
                -2
            ),
            clock,
            fill=(int(not inversed_colors),),
            font=CLOCK_FONT
        )


# class DisplayIssuePreview(Display):

#     def __init__(self, issue):
#         super().__init__()

#         project_key, issue_code = issue.key.lower().split("-")
