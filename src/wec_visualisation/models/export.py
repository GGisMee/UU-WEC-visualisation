from pathlib import Path
from itertools import count
import tomli_w
import zipfile
from typing import Protocol, Callable, Any
from matplotlib.figure import Figure


def _find_working_filename(path: Path | str, name: str, suffix: str) -> Path:
    """Finds name/path_i where i is number"""
    base_path = Path(path)
    
    # Searches for base name first
    if not (first_choice := base_path / f"{name}.{suffix}").exists():
        return first_choice
        
    # Generate e.g. 'output_1.json', 'output_2.json', and so on.
    for i in count(1):
        filepath = base_path / f"output_{i}.{suffix}"
        if not filepath.exists():
            return filepath
    return base_path/f"{name}.{suffix}"

class FileSaver(Protocol):
    append: Callable[..., None]
    def save(self, path: Path | str, name: str | None = None) -> bool: ...
    def clear(self) -> None: ...


class TomlSave(FileSaver):
    def __init__(self):
        """Saves datapoints for later exportation to json"""
        self.data_dict = {}
        self.units = {}
        self.significant_digits = 5
        
    def append(self, key: str, value: Any, unit: str | None = None) -> None:
        if not key:
            raise ValueError("Expected non empty key. For example: 'config.strength'")

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            # Format to significant digits, strip trailing zeros/points via float()
            formatted_value = float(f"{value:.{self.significant_digits}g}")
        else:
            formatted_value = value

        *path_parts, final_key = key.split('.')
        current = self.data_dict
        for subkey in path_parts: # Iterate deeper in nested dict
            # if key not there, create it
            current = current.setdefault(subkey, {})
        
        current[final_key] = formatted_value
        if unit:
            self.units[key] = unit

    def save(self, path: Path|str = '.', name: str | None = None) -> bool:
        if len(self.data_dict.keys()) == 0:
            return False
        if name:
            filepath = Path(path) / name
        else:
            filepath = _find_working_filename(path, "data", suffix='toml') 
            
        toml_str = tomli_w.dumps(self.data_dict)
        lines = toml_str.splitlines()
        
        for full_key, unit in self.units.items():
            parts = full_key.split('.')
            final_key = parts[-1]
            section = ".".join(parts[:-1])
            
            current_section = ""
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                if line_stripped.startswith('[') and line_stripped.endswith(']'):
                    current_section = line_stripped[1:-1]
                elif current_section == section:
                    if line_stripped.startswith(final_key + " =") or line_stripped.startswith('"' + final_key + '" ='):
                        lines[i] = line + f" # [{unit}]"
                        break
                        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines) + "\n")
        return True

    def clear(self):
        self.data_dict = {}
        self.units = {}

class PlotSave(FileSaver):
    def __init__(self) -> None:
        self.figures: dict[str, Figure] = {}

    def append(self, name: str, figure: Figure) -> None:
        self.figures[name] = figure

    def save(self, path: Path | str, name: str | None = None) -> bool:
        if not self.figures:
            return False
        
        base_path = Path(path)
        if name:
            target_dir = base_path / name
        else:
            target_dir = base_path
            
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for fig_name, figure in self.figures.items():
            # Ensure correct extension (default to .png)
            filename = fig_name if fig_name.endswith(('.png', '.pdf', '.svg', '.jpg', '.jpeg')) else f"{fig_name}.png"
            figure.savefig(target_dir / filename, bbox_inches='tight', dpi=300)
        return True

    def clear(self):
        self.figures = {}


class CsvSave(FileSaver):
    def __init__(self) -> None:
        self.rows: list[list[Any]] = []
        self.headers: list[str] = []

    def append(self, headers: list[str], rows: list[list[Any]]) -> None:
        self.headers = headers
        self.rows = rows

    def save(self, path: Path | str, name: str | None = None) -> bool:
        if not self.rows:
            return False
        import csv
        final_name = name if name is not None else "data.csv"
        if not final_name.endswith('.csv'):
            final_name += '.csv'
        filepath = Path(path) / final_name
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if self.headers:
                writer.writerow(self.headers)
            writer.writerows(self.rows)
        return True


    def clear(self):
        self.headers= []
        self.rows = []

class PdfSave(FileSaver):
    def __init__(self) -> None:
        self.elements: list[tuple[str, Any]] = []

    def append(self, element_type: str, content: Any) -> None:
        """
        element_type: 'heading', 'text', or 'image'
        content: string (for text/heading) or matplotlib Figure/file path (for image)
        """
        self.elements.append((element_type, content))

    def save(self, path: Path | str, name: str | None = None) -> bool:
        if not self.elements:
            return False
        from matplotlib.backends.backend_pdf import PdfPages
        import matplotlib.image as mpimg
        import textwrap
        import io

        final_name = name if name is not None else "report.pdf"
        if not final_name.endswith('.pdf'):
            final_name += '.pdf'
        filepath = Path(path) / final_name
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        pages: list[Figure] = []
        
        def create_new_page():
            fig = Figure(figsize=(8.27, 11.69))  # A4 Size
            ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
            ax.axis('off')
            return fig, ax

        fig, ax = create_new_page()
        pages.append(fig)
        
        y_pos = 0.9
        margin_x = 0.1
        
        for elem_type, content in self.elements:
            if elem_type == 'heading':
                if y_pos < 0.1:
                    fig, ax = create_new_page()
                    pages.append(fig)
                    y_pos = 0.9
                ax.text(margin_x, y_pos, content, fontsize=18, fontweight='bold', 
                        va='top', ha='left', transform=ax.transAxes)
                y_pos -= 0.04
                
            elif elem_type == 'text':
                wrapped_lines = textwrap.wrap(content, width=80)
                for line in wrapped_lines:
                    if y_pos < 0.05:
                        fig, ax = create_new_page()
                        pages.append(fig)
                        y_pos = 0.9
                    ax.text(margin_x, y_pos, line, fontsize=11, 
                            va='top', ha='left', transform=ax.transAxes)
                    y_pos -= 0.016
                y_pos -= 0.012
                
            elif elem_type == 'image':
                if y_pos < 0.4:
                    fig, ax = create_new_page()
                    pages.append(fig)
                    y_pos = 0.9
                
                image_y = y_pos - 0.35
                inset_ax = fig.add_axes((margin_x, image_y, 0.8, 0.35))
                inset_ax.axis('off')
                
                if hasattr(content, 'savefig') or isinstance(content, Figure):
                    buf = io.BytesIO()
                    content.savefig(buf, format='png', bbox_inches='tight', dpi=300)
                    buf.seek(0)
                    img = mpimg.imread(buf, format='png')
                    inset_ax.imshow(img)
                else:
                    img = mpimg.imread(content)
                    inset_ax.imshow(img)
                
                y_pos -= 0.38
        
        with PdfPages(filepath) as pdf:
            for page_fig in pages:
                pdf.savefig(page_fig, dpi=300)
                page_fig.clear()
        return True

    def clear(self):
        self.elements = []


class Saver:
    def __init__(self) -> None:
        self.toml = TomlSave()
        self.plots = PlotSave()
        self.csv = CsvSave()
        self.pdf = PdfSave()

    def save(self, path: Path | str = '.') -> bool:
        import tempfile
        base_path = Path(path)
        base_path.mkdir(parents=True, exist_ok=True)
        
        zip_filepath = base_path / "simulation_results.zip"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Save all results to the temporary directory
            self.toml.save(tmp_path, "results.toml")
            self.plots.save(tmp_path, "plots")
            self.csv.save(tmp_path, "data.csv")
            self.pdf.save(tmp_path, "report.pdf")
            
            # Pack them into simulation_results.zip
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file in tmp_path.rglob('*'):
                    if file.is_file():
                        zf.write(file, file.relative_to(tmp_path))
                        
        return True


if __name__ == '__main__':
    # Test simulation save run
    import matplotlib.pyplot as plt
    saver = Saver()
    
    # 1. Add TOML data
    saver.toml.append('config.simulation.name', "UU-WEC Test")
    saver.toml.append('results.energy_output', 450.2)
    
    # 2. Add CSV data
    saver.csv.append(
        headers=["time", "power"],
        rows=[
            [0.0, 12.5],
            [1.0, 15.3]
        ]
    )
    
    # 3. Add plots and pdf pages
    fig1, ax1 = plt.subplots()
    ax1.plot([0, 1], [12.5, 15.3])
    ax1.set_title("Power over Time")
    
    saver.plots.append("power_curve", fig1)
    
    # Generate markdown-style PDF document
    saver.pdf.append("heading", "Simulation Report")
    saver.pdf.append("text", "This is a sample document displaying WEC simulation outcomes. Below is the generated power output over time:")
    saver.pdf.append("image", fig1)
    saver.pdf.append("text", "The graph shows the power curve rising to a peak resonance frequency before leveling out as parameters converge.")
    
    # Save everything into the zip
    saver.save()
    print("Saved simulation_results.zip successfully.")