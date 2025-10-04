#!/usr/bin/env python3
"""
Generate Test Reports

Command-line script to generate HTML and PDF reports from test results.
Supports multiple testing frameworks and output formats.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from reports import ReportGenerator, ReportType
from reports.json_parser import TestFramework

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate test reports from JSON results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate HTML report from Playwright results
  python generate_report.py --input results.json --framework playwright --output-dir reports/

  # Generate both HTML and PDF reports
  python generate_report.py --input results.json --framework pytest --type both

  # Generate combined report from multiple files
  python generate_report.py --combined --input-files playwright:results1.json pytest:results2.json

  # Custom output name
  python generate_report.py --input results.json --framework appium --output-name mobile_test_report
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--input', '-i',
        type=str,
        help='Path to test results JSON file'
    )
    input_group.add_argument(
        '--input-files',
        nargs='+',
        help='Multiple input files in format framework:file_path (for combined reports)'
    )
    input_group.add_argument(
        '--combined', '-c',
        action='store_true',
        help='Generate combined report from multiple files (use with --input-files)'
    )
    
    # Framework
    parser.add_argument(
        '--framework', '-f',
        type=str,
        choices=['playwright', 'pytest', 'appium', 'security'],
        help='Testing framework used (required for single file input)'
    )
    
    # Output options
    parser.add_argument(
        '--type', '-t',
        type=str,
        choices=['html', 'pdf', 'both'],
        default='html',
        help='Report type to generate (default: html)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='reports',
        help='Output directory for reports (default: reports)'
    )
    
    parser.add_argument(
        '--output-name', '-n',
        type=str,
        help='Custom output filename (without extension)'
    )
    
    # Additional options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress output except errors'
    )
    
    return parser.parse_args()


def setup_logging(verbose: bool, quiet: bool):
    """Setup logging based on verbosity flags"""
    if quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)


def parse_input_files(input_files: List[str]) -> List[Dict]:
    """Parse input files in format framework:file_path"""
    parsed_files = []
    
    for input_file in input_files:
        if ':' not in input_file:
            logger.error(f"Invalid input file format: {input_file}")
            logger.error("Expected format: framework:file_path")
            sys.exit(1)
        
        framework_str, file_path = input_file.split(':', 1)
        
        try:
            framework = TestFramework(framework_str.lower())
        except ValueError:
            logger.error(f"Unsupported framework: {framework_str}")
            logger.error(f"Supported frameworks: {[f.value for f in TestFramework]}")
            sys.exit(1)
        
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"Input file not found: {file_path}")
            sys.exit(1)
        
        parsed_files.append({
            'file': file_path,
            'framework': framework
        })
    
    return parsed_files


def main():
    """Main function"""
    args = parse_arguments()
    setup_logging(args.verbose, args.quiet)
    
    try:
        # Initialize report generator
        generator = ReportGenerator(output_dir=args.output_dir)
        
        # Parse report type
        report_type = ReportType(args.type)
        
        # Generate report based on input type
        if args.input:
            # Single file input
            if not args.framework:
                logger.error("Framework is required for single file input")
                sys.exit(1)
            
            input_file = Path(args.input)
            if not input_file.exists():
                logger.error(f"Input file not found: {input_file}")
                sys.exit(1)
            
            framework = TestFramework(args.framework.lower())
            
            logger.info(f"Generating {args.type} report from {input_file}")
            logger.info(f"Framework: {framework.value}")
            
            generated_files = generator.generate_from_file(
                test_results_file=input_file,
                framework=framework,
                report_type=report_type,
                output_name=args.output_name
            )
            
        elif args.input_files:
            # Multiple files input
            parsed_files = parse_input_files(args.input_files)
            
            logger.info(f"Generating combined {args.type} report from {len(parsed_files)} files")
            for file_info in parsed_files:
                logger.info(f"  - {file_info['framework'].value}: {file_info['file']}")
            
            generated_files = generator.generate_combined_report(
                test_files=parsed_files,
                report_type=report_type,
                output_name=args.output_name
            )
        
        else:
            logger.error("No input specified")
            sys.exit(1)
        
        # Report success
        logger.info("Report generation completed successfully!")
        for report_format, file_path in generated_files.items():
            logger.info(f"  {report_format.upper()}: {file_path}")
        
        # Print summary if not quiet
        if not args.quiet:
            print("\n" + "="*50)
            print("REPORT GENERATION SUMMARY")
            print("="*50)
            for report_format, file_path in generated_files.items():
                print(f"{report_format.upper()} Report: {file_path}")
            print("="*50)
        
    except KeyboardInterrupt:
        logger.info("Report generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        if args.verbose:
            logger.exception("Full error details:")
        sys.exit(1)


if __name__ == '__main__':
    main()