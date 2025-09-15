"""
Data Visualization Service
Handles chart generation and data visualization
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import statistics

@dataclass
class ChartData:
    """Chart data structure"""
    labels: List[str]
    datasets: List[Dict[str, Any]]
    title: str = ""
    type: str = "bar"

@dataclass
class ProcessingStats:
    """Processing statistics"""
    total_files: int
    completed_files: int
    failed_files: int
    total_keywords: int
    processed_keywords: int
    total_batches: int
    completed_batches: int
    failed_batches: int
    processing_time: str
    avg_keywords_per_file: float
    success_rate: float
    keywords_per_second: float

class DataVisualization:
    """Data visualization service"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_processing_stats(self, job_results: List[Dict[str, Any]]) -> ProcessingStats:
        """
        Generate processing statistics from job results

        Args:
            job_results: List of job result entries

        Returns:
            ProcessingStats object
        """
        try:
            # Filter out non-keyword entries (like error messages)
            keyword_entries = [r for r in job_results if isinstance(r, dict) and 'keyword' in r]
            error_entries = [r for r in job_results if isinstance(r, dict) and 'error' in r]

            # Calculate basic statistics
            total_keywords = len(keyword_entries)
            processed_keywords = len([r for r in keyword_entries if 'kdroi' in r])

            # File statistics (assuming file info is available)
            files_processed = set()
            for entry in job_results:
                if isinstance(entry, dict) and 'file' in entry:
                    files_processed.add(entry['file'])

            total_files = len(files_processed)
            completed_files = len([r for r in job_results if isinstance(r, dict) and r.get('status') == 'completed'])
            failed_files = len([r for r in job_results if isinstance(r, dict) and r.get('status') == 'failed'])

            # Batch statistics
            total_batches = (total_keywords + 499) // 500  # Ceiling division
            completed_batches = processed_keywords // 500
            failed_batches = total_batches - completed_batches

            # Calculate rates
            success_rate = (completed_files / total_files * 100) if total_files > 0 else 0
            avg_keywords_per_file = total_keywords / total_files if total_files > 0 else 0

            # Estimate processing speed (placeholder - would need actual timing data)
            keywords_per_second = processed_keywords / 60 if processed_keywords > 0 else 0  # Assume 60 seconds

            return ProcessingStats(
                total_files=total_files,
                completed_files=completed_files,
                failed_files=failed_files,
                total_keywords=total_keywords,
                processed_keywords=processed_keywords,
                total_batches=total_batches,
                completed_batches=completed_batches,
                failed_batches=failed_batches,
                processing_time="0s",  # Would calculate from actual timestamps
                avg_keywords_per_file=avg_keywords_per_file,
                success_rate=success_rate,
                keywords_per_second=keywords_per_second
            )

        except Exception as e:
            self.logger.error(f"Failed to generate processing stats: {e}")
            return ProcessingStats(0, 0, 0, 0, 0, 0, 0, 0, "0s", 0, 0, 0)

    def create_progress_chart(self, stats: ProcessingStats) -> ChartData:
        """
        Create progress chart data

        Args:
            stats: Processing statistics

        Returns:
            ChartData for progress chart
        """
        return ChartData(
            labels=['已完成', '失败', '剩余'],
            datasets=[{
                'data': [
                    stats.completed_files,
                    stats.failed_files,
                    stats.total_files - stats.completed_files - stats.failed_files
                ],
                'backgroundColor': [
                    '#198754',  # Success green
                    '#dc3545',  # Danger red
                    '#6c757d'   # Secondary gray
                ],
                'borderWidth': 0
            }],
            title="文件处理进度",
            type="doughnut"
        )

    def create_batch_progress_chart(self, stats: ProcessingStats) -> ChartData:
        """
        Create batch progress chart data

        Args:
            stats: Processing statistics

        Returns:
            ChartData for batch progress chart
        """
        return ChartData(
            labels=['已完成批次', '失败批次', '剩余批次'],
            datasets=[{
                'data': [
                    stats.completed_batches,
                    stats.failed_batches,
                    stats.total_batches - stats.completed_batches - stats.failed_batches
                ],
                'backgroundColor': [
                    '#0d6efd',  # Primary blue
                    '#ffc107',  # Warning yellow
                    '#e9ecef'   # Light gray
                ],
                'borderWidth': 0
            }],
            title="批次处理进度",
            type="doughnut"
        )

    def create_keyword_distribution_chart(self, keyword_data: List[Dict[str, Any]]) -> ChartData:
        """
        Create keyword distribution chart by Kdroi ranges

        Args:
            keyword_data: List of keyword entries

        Returns:
            ChartData for distribution chart
        """
        try:
            # Define Kdroi ranges
            ranges = {
                '0-10': 0,
                '10-50': 0,
                '50-100': 0,
                '100-500': 0,
                '500+': 0
            }

            # Count keywords in each range
            for entry in keyword_data:
                if isinstance(entry, dict) and 'kdroi' in entry:
                    kdroi = entry['kdroi']
                    if kdroi < 10:
                        ranges['0-10'] += 1
                    elif kdroi < 50:
                        ranges['10-50'] += 1
                    elif kdroi < 100:
                        ranges['50-100'] += 1
                    elif kdroi < 500:
                        ranges['100-500'] += 1
                    else:
                        ranges['500+'] += 1

            return ChartData(
                labels=list(ranges.keys()),
                datasets=[{
                    'data': list(ranges.values()),
                    'backgroundColor': [
                        '#dc3545',  # Red (low value)
                        '#fd7e14',  # Orange
                        '#ffc107',  # Yellow
                        '#20c997',  # Teal
                        '#198754'   # Green (high value)
                    ],
                    'borderWidth': 0
                }],
                title="Kdroi值分布",
                type="bar"
            )

        except Exception as e:
            self.logger.error(f"Failed to create distribution chart: {e}")
            return ChartData([], [], "Kdroi值分布", "bar")

    def create_performance_chart(self, stats: ProcessingStats) -> ChartData:
        """
        Create performance metrics chart

        Args:
            stats: Processing statistics

        Returns:
            ChartData for performance chart
        """
        return ChartData(
            labels=['成功率', '平均每文件关键词数', '每秒处理数'],
            datasets=[{
                'data': [
                    round(stats.success_rate, 1),
                    round(stats.avg_keywords_per_file, 1),
                    round(stats.keywords_per_second, 1)
                ],
                'backgroundColor': [
                    '#198754',  # Green
                    '#0d6efd',  # Blue
                    '#6f42c1'   # Purple
                ],
                'borderWidth': 0
            }],
            title="性能指标",
            type="bar"
        )

    def create_time_series_chart(self, job_results: List[Dict[str, Any]]) -> ChartData:
        """
        Create time series chart for processing timeline

        Args:
            job_results: List of job result entries with timestamps

        Returns:
            ChartData for time series chart
        """
        try:
            # Group by time periods (simplified - would need actual timestamps)
            time_periods = ['开始', '25%', '50%', '75%', '完成']
            progress_data = [0, 25, 50, 75, 100]

            return ChartData(
                labels=time_periods,
                datasets=[{
                    'label': '处理进度',
                    'data': progress_data,
                    'borderColor': '#0d6efd',
                    'backgroundColor': 'rgba(13, 110, 253, 0.1)',
                    'fill': True,
                    'tension': 0.4
                }],
                title="处理时间线",
                type="line"
            )

        except Exception as e:
            self.logger.error(f"Failed to create time series chart: {e}")
            return ChartData([], [], "处理时间线", "line")

    def create_top_keywords_chart(self, keyword_data: List[Dict[str, Any]], top_n: int = 10) -> ChartData:
        """
        Create top keywords by Kdroi chart

        Args:
            keyword_data: List of keyword entries
            top_n: Number of top keywords to show

        Returns:
            ChartData for top keywords chart
        """
        try:
            # Sort keywords by Kdroi and get top N
            sorted_keywords = sorted(
                [entry for entry in keyword_data if isinstance(entry, dict) and 'kdroi' in entry],
                key=lambda x: x['kdroi'],
                reverse=True
            )[:top_n]

            labels = [entry['keyword'][:20] + '...' if len(entry['keyword']) > 20 else entry['keyword']
                     for entry in sorted_keywords]
            values = [entry['kdroi'] for entry in sorted_keywords]

            return ChartData(
                labels=labels,
                datasets=[{
                    'data': values,
                    'backgroundColor': '#0d6efd',
                    'borderColor': '#0a58ca',
                    'borderWidth': 1
                }],
                title=f"Top {top_n} 关键词 (按Kdroi值)",
                type="bar"
            )

        except Exception as e:
            self.logger.error(f"Failed to create top keywords chart: {e}")
            return ChartData([], [], f"Top {top_n} 关键词", "bar")

    def generate_dashboard_data(self, job_id: str, job_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate complete dashboard data

        Args:
            job_id: Job ID
            job_results: List of job result entries

        Returns:
            Complete dashboard data dictionary
        """
        try:
            # Generate statistics
            stats = self.generate_processing_stats(job_results)

            # Extract keyword data
            keyword_data = [r for r in job_results if isinstance(r, dict) and 'keyword' in r]

            # Generate charts
            charts = {
                'progress': self.create_progress_chart(stats).__dict__,
                'batch_progress': self.create_batch_progress_chart(stats).__dict__,
                'distribution': self.create_keyword_distribution_chart(keyword_data).__dict__,
                'performance': self.create_performance_chart(stats).__dict__,
                'timeline': self.create_time_series_chart(job_results).__dict__,
                'top_keywords': self.create_top_keywords_chart(keyword_data).__dict__
            }

            # Generate summary
            summary = {
                'total_files': stats.total_files,
                'completed_files': stats.completed_files,
                'failed_files': stats.failed_files,
                'total_keywords': stats.total_keywords,
                'processed_keywords': stats.processed_keywords,
                'success_rate': round(stats.success_rate, 1),
                'avg_keywords_per_file': round(stats.avg_keywords_per_file, 1),
                'processing_time': stats.processing_time,
                'job_id': job_id,
                'generated_at': datetime.now().isoformat()
            }

            return {
                'summary': summary,
                'stats': stats.__dict__,
                'charts': charts,
                'job_id': job_id
            }

        except Exception as e:
            self.logger.error(f"Failed to generate dashboard data: {e}")
            return {
                'error': str(e),
                'job_id': job_id
            }

    def export_chart_data(self, chart_data: ChartData, format: str = 'json') -> str:
        """
        Export chart data in specified format

        Args:
            chart_data: Chart data to export
            format: Export format ('json', 'csv')

        Returns:
            Exported data string
        """
        try:
            if format.lower() == 'json':
                return json.dumps(chart_data.__dict__, indent=2, ensure_ascii=False)

            elif format.lower() == 'csv':
                # Simple CSV export for chart data
                lines = ['Label,Value']
                for i, label in enumerate(chart_data.labels):
                    value = chart_data.datasets[0]['data'][i]
                    lines.append(f'"{label}",{value}')
                return '\n'.join(lines)

            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            self.logger.error(f"Failed to export chart data: {e}")
            return ""

# Global visualization service instance
visualization_service = DataVisualization()