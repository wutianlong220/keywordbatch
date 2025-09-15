"""
Export Manager for Multi-format Data Export
Handles export to Excel, CSV, JSON, and other formats
"""

import json
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
from dataclasses import dataclass

@dataclass
class ExportOptions:
    """Export configuration options"""
    format: str = 'xlsx'  # xlsx, csv, json, html, txt
    include_original: bool = True
    include_calculated: bool = True
    include_links: bool = True
    include_metadata: bool = True
    template_name: Optional[str] = None
    custom_columns: Optional[List[str]] = None

class ExportManager:
    """Multi-format export management system"""

    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Define export templates
        self.templates = {
            'basic': {
                'columns': ['keyword', 'volume', 'cpc', 'difficulty', 'kdroi'],
                'description': 'Basic keyword data with Kdroi calculation'
            },
            'detailed': {
                'columns': ['keyword', 'translation', 'volume', 'cpc', 'difficulty', 'kdroi'],
                'description': 'Detailed data with translations'
            },
            'complete': {
                'columns': ['keyword', 'translation', 'volume', 'cpc', 'difficulty', 'kdroi',
                          'google_search_link', 'google_trends_link', 'ahrefs_link'],
                'description': 'Complete data with all links and translations'
            },
            'links_only': {
                'columns': ['keyword', 'google_search_link', 'google_trends_link', 'ahrefs_link'],
                'description': 'Only keywords and generated links'
            },
            'analysis': {
                'columns': ['keyword', 'volume', 'cpc', 'difficulty', 'kdroi'],
                'description': 'Data optimized for analysis'
            }
        }

    def export_data(self, data: List[Dict[str, Any]], filename: str, options: ExportOptions) -> str:
        """
        Export data to specified format

        Args:
            data: Data to export
            filename: Output filename (without extension)
            options: Export options

        Returns:
            Path to exported file
        """
        try:
            # Prepare data for export
            export_data = self.prepare_export_data(data, options)

            # Generate full filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            full_filename = f"{filename}_{timestamp}.{options.format}"
            output_path = self.output_dir / full_filename

            # Export based on format
            if options.format.lower() == 'xlsx':
                self.export_to_excel(export_data, output_path, options)
            elif options.format.lower() == 'csv':
                self.export_to_csv(export_data, output_path, options)
            elif options.format.lower() == 'json':
                self.export_to_json(export_data, output_path, options)
            elif options.format.lower() == 'html':
                self.export_to_html(export_data, output_path, options)
            elif options.format.lower() == 'txt':
                self.export_to_txt(export_data, output_path, options)
            else:
                raise ValueError(f"Unsupported export format: {options.format}")

            self.logger.info(f"Data exported to: {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            raise

    def prepare_export_data(self, data: List[Dict[str, Any]], options: ExportOptions) -> List[Dict[str, Any]]:
        """
        Prepare data for export based on options

        Args:
            data: Original data
            options: Export options

        Returns:
            Prepared data for export
        """
        try:
            # Filter out non-keyword entries
            keyword_data = [entry for entry in data if isinstance(entry, dict) and 'keyword' in entry]

            # Apply template if specified
            if options.template_name and options.template_name in self.templates:
                template = self.templates[options.template_name]
                columns = template['columns']
            elif options.custom_columns:
                columns = options.custom_columns
            else:
                columns = self.get_default_columns(options)

            # Prepare each row
            export_data = []
            for entry in keyword_data:
                row = {}

                for column in columns:
                    if column in entry:
                        row[column] = entry[column]
                    else:
                        row[column] = None

                export_data.append(row)

            return export_data

        except Exception as e:
            self.logger.error(f"Failed to prepare export data: {e}")
            return []

    def get_default_columns(self, options: ExportOptions) -> List[str]:
        """Get default columns based on export options"""
        columns = ['keyword']

        if options.include_original:
            columns.extend(['volume', 'cpc', 'difficulty'])

        if options.include_calculated:
            columns.append('kdroi')

        if options.include_links:
            columns.extend(['google_search_link', 'google_trends_link', 'ahrefs_link'])

        return columns

    def export_to_excel(self, data: List[Dict[str, Any]], output_path: Path, options: ExportOptions):
        """Export data to Excel format"""
        try:
            df = pd.DataFrame(data)

            # Create Excel writer with formatting
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Main data sheet
                df.to_excel(writer, sheet_name='Keywords', index=False)

                # Get workbook and worksheet for formatting
                workbook = writer.book
                worksheet = writer.sheets['Keywords']

                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

                # Add summary sheet if metadata is included
                if options.include_metadata:
                    summary_data = {
                        'Metric': ['Total Keywords', 'Export Date', 'Format', 'Template'],
                        'Value': [
                            len(data),
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            options.format,
                            options.template_name or 'Custom'
                        ]
                    }
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)

                # Add statistics sheet if calculated data is included
                if options.include_calculated and data:
                    stats_data = self.calculate_export_statistics(data)
                    stats_df = pd.DataFrame(list(stats_data.items()), columns=['Statistic', 'Value'])
                    stats_df.to_excel(writer, sheet_name='Statistics', index=False)

        except Exception as e:
            self.logger.error(f"Excel export failed: {e}")
            raise

    def export_to_csv(self, data: List[Dict[str, Any]], output_path: Path, options: ExportOptions):
        """Export data to CSV format"""
        try:
            if not data:
                return

            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write header
                writer.writeheader()

                # Write metadata comment if included
                if options.include_metadata:
                    csvfile.write(f"# Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    csvfile.write(f"# Total Keywords: {len(data)}\n")
                    csvfile.write(f"# Template: {options.template_name or 'Custom'}\n")

                # Write data
                writer.writerows(data)

        except Exception as e:
            self.logger.error(f"CSV export failed: {e}")
            raise

    def export_to_json(self, data: List[Dict[str, Any]], output_path: Path, options: ExportOptions):
        """Export data to JSON format"""
        try:
            export_dict = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'total_keywords': len(data),
                    'format': options.format,
                    'template': options.template_name or 'Custom',
                    'options': {
                        'include_original': options.include_original,
                        'include_calculated': options.include_calculated,
                        'include_links': options.include_links,
                        'include_metadata': options.include_metadata
                    }
                },
                'data': data
            }

            # Add statistics if calculated data is included
            if options.include_calculated and data:
                export_dict['statistics'] = self.calculate_export_statistics(data)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_dict, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"JSON export failed: {e}")
            raise

    def export_to_html(self, data: List[Dict[str, Any]], output_path: Path, options: ExportOptions):
        """Export data to HTML format"""
        try:
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>关键词导出报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>关键词处理结果报告</h1>

    <div class="summary">
        <h2>导出信息</h2>
        <p><strong>导出时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>关键词总数:</strong> {len(data)}</p>
        <p><strong>模板:</strong> {options.template_name or 'Custom'}</p>
    </div>
"""

            if data:
                # Add statistics if calculated data is included
                if options.include_calculated:
                    stats = self.calculate_export_statistics(data)
                    html_content += """
    <div class="summary">
        <h2>统计信息</h2>
        <table>
"""
                    for key, value in stats.items():
                        html_content += f"            <tr><td>{key}</td><td>{value}</td></tr>\n"
                    html_content += """
        </table>
    </div>
"""

                # Add data table
                html_content += """
    <h2>关键词数据</h2>
    <table>
        <thead>
            <tr>
"""
                for column in data[0].keys():
                    html_content += f"                <th>{column}</th>\n"
                html_content += """
            </tr>
        </thead>
        <tbody>
"""
                for row in data:
                    html_content += "            <tr>\n"
                    for value in row.values():
                        if isinstance(value, str) and value.startswith('http'):
                            html_content += f'                <td><a href="{value}" target="_blank">查看链接</a></td>\n'
                        else:
                            html_content += f"                <td>{value}</td>\n"
                    html_content += "            </tr>\n"
                html_content += """
        </tbody>
    </table>
"""

            html_content += """
</body>
</html>
"""

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

        except Exception as e:
            self.logger.error(f"HTML export failed: {e}")
            raise

    def export_to_txt(self, data: List[Dict[str, Any]], output_path: Path, options: ExportOptions):
        """Export data to plain text format"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # Write header
                f.write("=" * 50 + "\n")
                f.write("关键词处理结果报告\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"关键词总数: {len(data)}\n")
                f.write(f"模板: {options.template_name or 'Custom'}\n\n")

                # Write statistics if calculated data is included
                if options.include_calculated and data:
                    f.write("统计信息:\n")
                    f.write("-" * 20 + "\n")
                    stats = self.calculate_export_statistics(data)
                    for key, value in stats.items():
                        f.write(f"{key}: {value}\n")
                    f.write("\n")

                # Write data
                if data:
                    f.write("关键词数据:\n")
                    f.write("-" * 20 + "\n")

                    # Determine column widths
                    columns = data[0].keys()
                    column_widths = {col: max(len(col), max(len(str(row.get(col, ''))) for row in data)) + 2 for col in columns}

                    # Write header
                    header = " | ".join(col.ljust(column_widths[col]) for col in columns)
                    f.write(header + "\n")
                    f.write("-" * len(header) + "\n")

                    # Write data rows
                    for row in data:
                        row_data = " | ".join(str(row.get(col, '')).ljust(column_widths[col]) for col in columns)
                        f.write(row_data + "\n")

        except Exception as e:
            self.logger.error(f"TXT export failed: {e}")
            raise

    def calculate_export_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for export data"""
        try:
            stats = {
                'Total Keywords': len(data)
            }

            # Calculate numeric statistics
            numeric_fields = ['volume', 'cpc', 'difficulty', 'kdroi']
            for field in numeric_fields:
                values = [row.get(field, 0) for row in data if isinstance(row.get(field), (int, float))]
                if values:
                    stats[f'Avg {field.capitalize()}'] = round(sum(values) / len(values), 2)
                    stats[f'Max {field.capitalize()}'] = max(values)
                    stats[f'Min {field.capitalize()}'] = min(values)

            return stats

        except Exception as e:
            self.logger.error(f"Failed to calculate export statistics: {e}")
            return {}

    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available export templates"""
        return self.templates.copy()

    def get_supported_formats(self) -> List[str]:
        """Get supported export formats"""
        return ['xlsx', 'csv', 'json', 'html', 'txt']

    def create_export_template(self, name: str, columns: List[str], description: str = "") -> bool:
        """Create custom export template"""
        try:
            if name in self.templates:
                self.logger.warning(f"Template '{name}' already exists")
                return False

            self.templates[name] = {
                'columns': columns,
                'description': description
            }

            self.logger.info(f"Created export template: {name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create template: {e}")
            return False

    def batch_export(self, job_results: Dict[str, List[Dict[str, Any]]], base_filename: str, options: ExportOptions) -> List[str]:
        """Export multiple job results"""
        exported_files = []

        for job_id, data in job_results.items():
            try:
                filename = f"{base_filename}_{job_id}"
                file_path = self.export_data(data, filename, options)
                exported_files.append(file_path)
            except Exception as e:
                self.logger.error(f"Failed to export job {job_id}: {e}")

        return exported_files

# Global export manager instance
export_manager = ExportManager()