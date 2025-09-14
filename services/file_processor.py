"""
File Processing Service for Keyword Batch Processing Application
Handles file scanning, Excel reading, and data validation
"""

import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Data class for processing results"""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    total_rows: int = 0
    processed_rows: int = 0


class FileProcessor:
    """Service class for processing keyword files"""
    
    def __init__(self, input_folder: str, output_folder: str):
        """
        Initialize file processor
        
        Args:
            input_folder: Path to input folder containing Excel files
            output_folder: Path to output folder for processed files
        """
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.supported_extensions = {'.xlsx', '.xls', '.csv'}
        
        # Ensure output directory exists
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FileProcessor initialized - Input: {self.input_folder}, Output: {self.output_folder}")
    
    def scan_excel_files(self) -> List[Path]:
        """
        Scan input folder for Excel files
        
        Returns:
            List of Path objects for supported Excel files
        """
        if not self.input_folder.exists():
            raise FileNotFoundError(f"Input folder does not exist: {self.input_folder}")
        
        excel_files = []
        for file_path in self.input_folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                excel_files.append(file_path)
        
        logger.info(f"Found {len(excel_files)} Excel files in {self.input_folder}")
        return sorted(excel_files)
    
    def read_excel_file(self, file_path: Path) -> ProcessingResult:
        """
        Read Excel file and extract keyword data
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            ProcessingResult with extracted data or error message
        """
        try:
            logger.info(f"Reading Excel file: {file_path}")
            
            # Read Excel file with pandas
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Validate required columns
            required_columns = ['keyword', 'volume', 'cpc', 'difficulty']
            missing_columns = [col for col in required_columns if col.lower() not in [c.lower() for c in df.columns]]
            
            if missing_columns:
                return ProcessingResult(
                    success=False,
                    error_message=f"Missing required columns: {', '.join(missing_columns)}",
                    file_path=str(file_path)
                )
            
            # Standardize column names (case-insensitive)
            column_mapping = {}
            for col in df.columns:
                col_lower = col.lower()
                if col_lower in required_columns:
                    column_mapping[col] = col_lower
            
            df = df.rename(columns=column_mapping)
            
            # Filter to only required columns and convert to list of dictionaries
            df_filtered = df[required_columns].copy()
            
            # Data cleaning and validation
            df_filtered = self._clean_and_validate_data(df_filtered)
            
            # Convert to list of dictionaries
            data = df_filtered.to_dict('records')
            
            logger.info(f"Successfully read {len(data)} rows from {file_path}")
            
            return ProcessingResult(
                success=True,
                data=data,
                file_path=str(file_path),
                total_rows=len(df),
                processed_rows=len(data)
            )
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return ProcessingResult(
                success=False,
                error_message=f"Error reading file: {str(e)}",
                file_path=str(file_path)
            )
    
    def _clean_and_validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate keyword data
        
        Args:
            df: DataFrame with raw keyword data
            
        Returns:
            Cleaned and validated DataFrame
        """
        # Remove rows with missing keywords
        df = df.dropna(subset=['keyword'])
        
        # Clean keyword text
        df['keyword'] = df['keyword'].astype(str).str.strip()
        df = df[df['keyword'] != '']
        
        # Convert numeric columns
        numeric_columns = ['volume', 'cpc', 'difficulty']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with invalid numeric data
        df = df.dropna(subset=numeric_columns)
        
        # Ensure positive values
        for col in numeric_columns:
            df = df[df[col] >= 0]
        
        return df
    
    def create_batches(self, data: List[Dict[str, Any]], batch_size: int = 500) -> List[List[Dict[str, Any]]]:
        """
        Split data into batches for processing
        
        Args:
            data: List of keyword dictionaries
            batch_size: Size of each batch
            
        Returns:
            List of batches
        """
        batches = []
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batches.append(batch)
        
        logger.info(f"Created {len(batches)} batches of size {batch_size}")
        return batches
    
    def save_processed_data(self, data: List[Dict[str, Any]], output_filename: str) -> Path:
        """
        Save processed data to output folder
        
        Args:
            data: List of processed keyword dictionaries
            output_filename: Name for output file
            
        Returns:
            Path to saved file
        """
        output_path = self.output_folder / output_filename
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Save as Excel file
        df.to_excel(output_path, index=False)
        
        logger.info(f"Saved processed data to {output_path}")
        return output_path
    
    def process_file(self, file_path: Path, batch_size: int = 500) -> Tuple[ProcessingResult, List[List[Dict[str, Any]]]]:
        """
        Process a single Excel file
        
        Args:
            file_path: Path to Excel file
            batch_size: Size of processing batches
            
        Returns:
            Tuple of (ProcessingResult, List of batches)
        """
        logger.info(f"Processing file: {file_path}")
        
        # Read the file
        result = self.read_excel_file(file_path)
        
        if not result.success:
            return result, []
        
        # Create batches
        batches = self.create_batches(result.data, batch_size)
        
        return result, batches
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get basic information about a file
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file information
        """
        try:
            stat = file_path.stat()
            return {
                'name': file_path.name,
                'path': str(file_path),
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'extension': file_path.suffix.lower()
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {str(e)}")
            return {
                'name': file_path.name,
                'path': str(file_path),
                'size': 0,
                'modified': 0,
                'extension': file_path.suffix.lower(),
                'error': str(e)
            }