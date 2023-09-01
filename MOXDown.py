from typing import List
from enum import Enum, auto
import sys


# Compilation Configuration
DEBUG_MODE: bool = True
VERSION: float = "1.0"

# Gopher Configuration
GOPHER_HOST = "mox.vice.ar"
GOPHER_PORT = 70

# HTML Page Configuration
FONT_COLOR = "black" # HTML Color name or Hex
LINK_COLOR = "blue" # HTML Color name or Hex
VISITED_LINK_COLOR = "#ff00aa" # HTML Color name or Hex
BACKGROUND_COLOR = "#bbddff" # HTML Color name or Hex or Image Name
LIST_CHAR = "❧"
LINK_CHAR = "☞"


class TokenType(Enum):
    TEXT = auto()
    LINK = auto()
    HEADING1 = auto()
    HEADING2 = auto()
    HEADING3 = auto()
    LIST_ITEM = auto()
    PREFORMATTED = auto()
    HRULE = auto()
    IMAGE = auto()


class LineToken:
    '''A TextLine represents a line of readable text.
    '''
    def __init__(self, type: TokenType, tokens: str, original_line: str):
        # debug_log(f"[{type}] {original_line} {tokens}")
        self.__type: TokenType = type
        self.__tokens: List[str] = tokens
        self.__line: str = original_line

    def get_type(self) -> TokenType:
        return self.__type

    def get_token_count(self) -> int:
        return len(self.__tokens)

    def get_token_i(self, index: int) -> str:
        try:
            return self.__tokens[index]
        except IndexError:
            throw_error("Missing token for index {index} in line: {self.__line}")



def log_error(message: str) -> None:
    '''Throws an error as an uncatcheable exception.
    '''
    raise Exception(f"[ ERROR ]\n{message}")
    exit()  # <- Trucazo


def debug_log(message: str) -> None:
    '''Prints a message if the compiler was launched in debug mode.
    '''
    if DEBUG_MODE:
        print(message)


def get_file_name_without_suffix(filename: str) -> str:
    '''Removes the suffix of a filename.
    '''
    if "." in filename:
        filename = filename[::-1]
        filename = filename.split(".", maxsplit=2)[1]
        filename = filename[::-1]
    if "/" in filename:
        filename = filename.split("/")[-1]
    if "\\" in filename:
        filename = filename.split("\\")[-1]
    return filename


def load_mox_file(filename: str) -> List[str]:
    '''Loads a MoxDown file and returns its contents as a list of strings.
    Empty lines at the end are removed. Preformatted lines are returned as
    a single line.
    '''
    # Read file contents
    content = ""
    try:
        with open(filename, "r") as mox_file:
            content = mox_file.read()
            content = content + "\n"
    except Exception as e:
        throw_error(f"Error reading file {filename}: {e}")
    # Load lines
    lines = []
    current_line = ""
    preformatted_mode = False
    backtick_count = 0
    for char in content:
        # Add char to line
        current_line = current_line + char
        # Check for backticks for preformatted mode
        if char == '`':
            backtick_count += 1
            if backtick_count == 3:
                # Only set preformatted mode if ``` are the first chars
                # in the trimmed line.
                preformatted_mode = len(current_line.strip()) == 3
                backtick_count = 0
        # Not a backtick
        else:
            backtick_count = 0
            # Line break outside preformatted mode
            if char == '\n' and not preformatted_mode:
                lines.append(current_line.strip())
                current_line = ""
    # Remove empty lines at the end
    for i in range(len(lines) - 1, 0, -1):
        if not lines[i].strip():
            del lines[i]
        else:
            break
    return lines


def line_starts_with(line: str, prefix: str) -> bool:
    '''Returns if a line starts with the given prefix.
    '''
    if len(line) < len(prefix):
        return False
    return line[0:len(prefix)] == prefix


def remove_prefix(line: str, prefix: str) -> str:
    '''Removes a prefix from a line, if found.
    '''
    if not line_starts_with(line, prefix):
        return line
    else:
        return line[len(prefix):].strip()


def parse_document(lines: List[str]) -> List[LineToken]:
    '''Parses a document and returns a list of LineToken elements.
    '''
    tokens: List[LineToken] = []
    for line in lines:
        tokens.append(parse_line(line))
    return tokens


def parse_line(line: str) -> LineToken:
    '''Parses a line and returns it tokenized as a LineToken.
    '''
    line = line.strip()
    # Link line
    if line_starts_with(line, "=>"):
        tokens = line.split(maxsplit=2)
        url = tokens[1]
        if not "://" in url:
            throw_error(f"The link to {url} is missing the protocol (such as http://).")
        return LineToken(TokenType.LINK, tokens, line)
    # Header 3
    elif line_starts_with(line, "###"):
        return LineToken(TokenType.HEADING3, [remove_prefix(line, "###").strip()], line)
    # Header 2
    elif line_starts_with(line, "##"):
        return LineToken(TokenType.HEADING2, [remove_prefix(line, "##").strip()], line)
    # Header 1
    elif line_starts_with(line, "#"):
        return LineToken(TokenType.HEADING1, [remove_prefix(line, "#").strip()], line)
    # List Item
    elif line_starts_with(line, "*"):
        return LineToken(TokenType.LIST_ITEM, [remove_prefix(line, "*").strip()], line)
    # Preformatted Text
    elif line_starts_with(line, "```"):
        return LineToken(TokenType.PREFORMATTED, [line[3:-3].strip("\n\r")], line)
    # Horizontal Rule
    elif line == "---":
        return LineToken(TokenType.HRULE, [], line)
    # Image
    elif line_starts_with(line, "(img)"):
        tokens = line.split(maxsplit=2)
        return LineToken(TokenType.IMAGE, tokens, line)
    # Text
    else:
        return LineToken(TokenType.TEXT, [line.strip()], line)


def generate_files(filename: str) -> None:
    '''Given a filename it generates files for all the supported protocols.
    '''
    # Parse and load everything
    debug_log(f"Compiling: {filename}")
    filename_nosuffix: str = get_file_name_without_suffix(filename)
    lines: List[str] = load_mox_file(filename)
    line_tokens: List[LineToken] = parse_document(lines)

    # HTML
    document_filename = f"{filename_nosuffix}.html"
    debug_log(f"Generating HTML: {document_filename}")
    source: str = generate_html(line_tokens)
    with open(document_filename, "w") as source_file:
        source_file.write(source)

    # Gopher
    document_filename = f"{filename_nosuffix}.gph"
    debug_log(f"Generating Gopher: {document_filename}")
    source: str = generate_gopher(line_tokens)
    with open(document_filename, "w") as source_file:
        source_file.write(source)

    # Gemini
    document_filename = f"{filename_nosuffix}.gmi"
    debug_log(f"Generating Gemini: {document_filename}")
    source: str = generate_gemini(line_tokens)
    with open(document_filename, "w") as source_file:
        source_file.write(source)


def generate_html(line_tokens: List[LineToken]) -> str:
    '''Generates HTML source code from a list of line tokens.
    '''
    should_add_line_break_after: bool = False
    ignore_next_empty_line: bool = False
    title: str = ""
    body: str = ""
    for line_token in line_tokens:
        # Text Line
        if line_token.get_type() == TokenType.TEXT:
            if ignore_next_empty_line and len(line_token.get_token_i(0)) == 0:
                ignore_next_empty_line = False
                continue
            if should_add_line_break_after:
                body = body + "<br>"
            body = body + line_token.get_token_i(0) + "\n"
            should_add_line_break_after = True
            ignore_next_empty_line = False
        # Link Line
        elif line_token.get_type() == TokenType.LINK:
            if should_add_line_break_after:
                body = body + "<br>"
            url = line_token.get_token_i(1)
            if "mox://" in url:
                url = url.replace("mox://", "").replace(".mox", ".html")
            readable_text = url
            if line_token.get_token_count() > 2:
                readable_text = line_token.get_token_i(2)
            body = body + f"{LINK_CHAR} <a href={url}>{readable_text}</a>" + "\n"
            should_add_line_break_after = True
            ignore_next_empty_line = False
        # Header 1 Line
        elif line_token.get_type() == TokenType.HEADING1:
            body = body + "<h1>" + line_token.get_token_i(0) + "</h1>" + "\n"
            should_add_line_break_after = False
            ignore_next_empty_line = True
            if not title:
                title = line_token.get_token_i(0)
        # Header 2 Line
        elif line_token.get_type() == TokenType.HEADING2:
            body = body + "<h2>" + line_token.get_token_i(0) + "</h2>" + "\n"
            should_add_line_break_after = False
            ignore_next_empty_line = True
        # Header 3 Line
        elif line_token.get_type() == TokenType.HEADING3:
            body = body + "<h3>" + line_token.get_token_i(0) + "</h2>" + "\n"
            should_add_line_break_after = False
            ignore_next_empty_line = True
        # List Item
        elif line_token.get_type() == TokenType.LIST_ITEM:
            if should_add_line_break_after:
                body = body + "<br>"
            body = body + f"&emsp;{LIST_CHAR} " + line_token.get_token_i(0) + "\n"
            should_add_line_break_after = True
        # Preformatted Text
        elif line_token.get_type() == TokenType.PREFORMATTED:
            body = body + "<pre>" + line_token.get_token_i(0) + "</pre>" + "\n"
            should_add_line_break_after = False
            ignore_next_empty_line = True
        # Horizontal Rule
        elif line_token.get_type() == TokenType.HRULE:
            body = body + "<hr>" + "\n"
            should_add_line_break_after = False
            ignore_next_empty_line = True
        # Image
        elif line_token.get_type() == TokenType.IMAGE:
            if should_add_line_break_after:
                body = body + "<br>"
            body = body + f"<img src='{line_token.get_token_i(1)}' title='{line_token.get_token_i(2)}'>" + "\n"
            should_add_line_break_after = True
            ignore_next_empty_line = False
    # Header
    html: str = f"""
    <html>
        <!-- Generated with MoxDown {VERSION} -->
        <head>
            <title>{title}</title>
            <meta charset=\"utf-8\">
        </head>
    """
    # CSS
    html += """
        <style>
            body{
                padding: 1em;
            }
            img {
                max-width: 400px;
                max-height: 300px;
            }
            pre {
                background: white;
                padding: 0.5em;
            }
        </style>
    """
    # Body
    html += f"""
        <body bgcolor="{BACKGROUND_COLOR}" text="{FONT_COLOR}" link="{LINK_COLOR}" vlink="{VISITED_LINK_COLOR}">
        {body}
        </body>
        <html>
    """
    return html


def generate_gopher(line_tokens: List[LineToken]) -> str:
    '''Generates Gopher source code from a list of line tokens.
    '''
    body: str = ""
    for line_token in line_tokens:
        # Text Line
        if line_token.get_type() == TokenType.TEXT:
            body = body + f"i{line_token.get_token_i(0)}\t(NULL)\t{GOPHER_HOST}\t{GOPHER_PORT}\r\n"
        # Link Line
        elif line_token.get_type() == TokenType.LINK:
            url = line_token.get_token_i(1)
            if "mox://" in url:
                url = url.replace("mox://", "").replace(".mox", ".gph")
            readable_text = url
            if line_token.get_token_count() > 2:
                readable_text = line_token.get_token_i(2)
            body = body + f"1{readable_text}\t{url}\t{GOPHER_HOST}\t{GOPHER_PORT}\r\n"
        # Header 1 Line
        elif line_token.get_type() == TokenType.HEADING1:
            body = body + f"i=== {line_token.get_token_i(0)} ===\t(NULL)\t{GOPHER_HOST}\t{GOPHER_PORT}\r\n"
        # Header 2 Line
        elif line_token.get_type() == TokenType.HEADING2:
            body = body + f"i== {line_token.get_token_i(0)} ==\t(NULL)\t{GOPHER_HOST}\t{GOPHER_PORT}\r\n"
        # Header 3 Line
        elif line_token.get_type() == TokenType.HEADING3:
            body = body + f"i-- {line_token.get_token_i(0)} --\t(NULL)\t{GOPHER_HOST}\t{GOPHER_PORT}\r\n"
        # List Item
        elif line_token.get_type() == TokenType.LIST_ITEM:
            body = body + f"i - {line_token.get_token_i(0)}\t(NULL)\t{GOPHER_HOST}\t{GOPHER_PORT}\r\n"
        # Preformatted Text
        elif line_token.get_type() == TokenType.PREFORMATTED:
            lines = line_token.get_token_i(0).split("\n")
            for line in lines:
                while len(line) > 0:
                    body = body + f"i    {line[0:63]}\t(NULL)\t{GOPHER_HOST}\t{GOPHER_PORT}\r\n"
                    line = line[63:]
        # Horizontal Rule
        elif line_token.get_type() == TokenType.HRULE:
            body = body + f"i{('*' * 40)}\t(NULL)\t{GOPHER_HOST}\t{GOPHER_PORT}\r\n"
        # Image
        elif line_token.get_type() == TokenType.IMAGE:
            body = body + f"p[ {line_token.get_token_i(2)} ]\t{line_token.get_token_i(1)}\t{GOPHER_HOST}\t{GOPHER_PORT}\r\n"
    return body


def generate_gemini(line_tokens: List[LineToken]) -> str:
    '''Generates Gemini source code from a list of line tokens.
    '''
    body: str = ""
    for line_token in line_tokens:
        # Text Line
        if line_token.get_type() == TokenType.TEXT:
            body = body + f"{line_token.get_token_i(0)}\n"
        # Link Line
        elif line_token.get_type() == TokenType.LINK:
            url = line_token.get_token_i(1)
            if "mox://" in url:
                url = url.replace("mox://", "").replace(".mox", ".gmi")
            readable_text = url
            if line_token.get_token_count() > 2:
                readable_text = line_token.get_token_i(2)
            body = body + f"=> {url} {readable_text}\n"
        # Header 1 Line
        elif line_token.get_type() == TokenType.HEADING1:
            body = body + f"# {line_token.get_token_i(0)}\n"
        # Header 2 Line
        elif line_token.get_type() == TokenType.HEADING2:
            body = body + f"## {line_token.get_token_i(0)}\n"
        # Header 3 Line
        elif line_token.get_type() == TokenType.HEADING3:
            body = body + f"### {line_token.get_token_i(0)}\n"
        # List Item
        elif line_token.get_type() == TokenType.LIST_ITEM:
            body = body + f"* {line_token.get_token_i(0)}\n"
        # Preformatted Text
        elif line_token.get_type() == TokenType.PREFORMATTED:
            body = body + f"```{line_token.get_token_i(0)}```\n"
        # Horizontal Rule
        elif line_token.get_type() == TokenType.HRULE:
            body = body + f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n"
        # Image
        elif line_token.get_type() == TokenType.IMAGE:
            body = body + f"=> {line_token.get_token_i(1)} Image: {line_token.get_token_i(2)}\n"
    return body


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("")
        print(f"MOXDown {VERSION}, by Lartu")
        print("")
        print("Usage:")
        print("    python3 MOXDown.py <mox filename>")
        print("")
        print("Options:")
        print(f"-g     Set Gopher Host (default: {GOPHER_HOST})")
        print(f"-p     Set Gopher Port (default: {GOPHER_PORT})")
        print(f"-c     Set HTML Font Color (default: {FONT_COLOR})")
        print(f"-l     Set HTML Link Color (default: {LINK_COLOR})")
        print(f"-v     Set HTML Visited Link Color (default: {VISITED_LINK_COLOR})")
        print(f"-b     Set HTML Background Color (default: {BACKGROUND_COLOR})")
        print(f"-u     Set List Bullet Character (default: {LIST_CHAR})")
        print(f"-k     Set Link Indicator Character (default: {LINK_CHAR})")
        print("")
        print("NOTE: Don't leave any whitespace between flags and values.")
        print("Example:")
        print("    python3 MOXDown.py myfile.mox -gmysite.com -p70")
        print("")
    else:
        filename = sys.argv[1]
        for argument in sys.argv[2:]:
            if argument[0:2] == "-g":
                GOPHER_HOST = argument[2:]
            elif argument[0:2] == "-p":
                GOPHER_PORT = int(argument[2:])
            elif argument[0:2] == "-c":
                FONT_COLOR == argument[2:]
            elif argument[0:2] == "-l":
                LINK_COLOR = argument[2:]
            elif argument[0:2] == "-v":
                VISITED_LINK_COLOR = argument[2:]
            elif argument[0:2] == "-b":
                BACKGROUND_COLOR = argument[2:]
            elif argument[0:2] == "-u":
                LIST_CHAR = argument[2:]
            elif argument[0:2] == "-k":
                LINK_CHAR = argument[2:]
        generate_files(filename=filename)
