import sys
import os
import subprocess
import json
import traceback
import time

def debug(msg):
    """Print debug messages to stderr"""
    print(msg, file=sys.stderr, flush=True)

# Extension to script mapping - FORCE MANUFACTURING ANALYZER FOR STL
EXTENSION_MAP = {
    '.stl': 'analyze_stl_manufacturing.py',  # FORCE manufacturing analyzer
    '.step': 'analyze_step_simple.py',
    '.stp': 'analyze_step_simple.py',
    '.dxf': 'analyze_dxf_dwg.py',
    '.dwg': 'analyze_dxf_dwg.py',
    '.ai':  'analyze_ai_eps.py',
    '.eps': 'analyze_ai_eps.py',
}

def get_extension(path):
    ext = os.path.splitext(path)[1].lower()
    debug(f"File extension: {ext}")
    return ext

def error_response(message, **kwargs):
    """Create a standardized error response"""
    response = {
        "error": message,
        "analysis_time_ms": 0
    }
    response.update(kwargs)
    debug(f"Error: {message}")
    return json.dumps(response)

def verify_python_environment():
    """Verify Python environment and dependencies"""
    try:
        import numpy
        debug(f"NumPy version: {numpy.__version__}")
        return None
    except ImportError as e:
        return error_response(f"NumPy not installed: {str(e)}")

def run_analyzer(script_path, file_path, timeout=120):
    """Run an analyzer script and return its output."""
    start_time = time.time()
    debug(f"Starting analysis at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Verify Python environment
    env_error = verify_python_environment()
    if env_error:
        return env_error

    # Check script existence
    if not os.path.exists(script_path):
        return error_response(f"Analyzer script not found: {script_path}")

    # Check file existence and readability
    if not os.path.exists(file_path):
        return error_response(f"Input file not found: {file_path}")

    try:
        with open(file_path, 'rb') as f:
            if not f.read(1):
                return error_response("Input file is empty")
    except Exception as e:
        return error_response(f"Cannot read input file: {str(e)}")

    # Print debug info
    debug(f"Python executable: {sys.executable}")
    debug(f"Python version: {sys.version}")
    debug(f"Script path: {script_path}")
    debug(f"File path: {file_path}")
    debug(f"Working directory: {os.getcwd()}")

    try:
        # Import the analyzer module directly
        sys.path.insert(0, os.path.dirname(script_path))
        module_name = os.path.splitext(os.path.basename(script_path))[0]
        debug(f"Importing module: {module_name}")

        analyzer = __import__(module_name)
        debug("Module imported successfully")

        # Get analyze function based on file extension
        ext = get_extension(file_path)
        analyze_funcs = {
            '.stl': ['analyze_stl_with_manufacturing', 'analyze_stl', 'analyze_stl_simple'],
            '.step': ['analyze_step', 'analyze_step_simple'],
            '.stp': ['analyze_step', 'analyze_step_simple'],
            '.dxf': ['analyze_dxf'],
            '.dwg': ['analyze_dxf'],
            '.ai': ['analyze_ai_eps', 'analyze'],
            '.eps': ['analyze_ai_eps', 'analyze']
        }

        # Try each possible function name
        func_names = analyze_funcs.get(ext, ['analyze'])
        for func_name in func_names:
            if hasattr(analyzer, func_name):
                debug(f"Using {func_name} function")
                analyze_func = getattr(analyzer, func_name)
                result = analyze_func(file_path)
                break
        else:
            raise AttributeError(f"No suitable analyze function found in {module_name} for {ext} files")

        debug("Analysis completed successfully")

        # Ensure result is JSON serializable
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError as e:
                return error_response("Analyzer returned invalid JSON", output=result)

        # Add analysis time
        result['analysis_time_ms'] = int((time.time() - start_time) * 1000)
        return json.dumps(result)

    except ImportError as e:
        return error_response(f"Failed to import analyzer module: {str(e)}")
    except Exception as e:
        debug(f"Error details: {traceback.format_exc()}")
        return error_response(str(e), traceback=traceback.format_exc())

def main():
    try:
        debug("\n=== Analysis Start ===")
        debug(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        debug(f"Arguments: {sys.argv}")
        debug(f"Working directory: {os.getcwd()}")

        if len(sys.argv) < 2:
            print(error_response("No input file specified"))
            return 1

        file_path = sys.argv[1]
        if not os.path.exists(file_path):
            print(error_response(f"File not found: {file_path}"))
            return 1

        ext = get_extension(file_path)
        analyzer_script = EXTENSION_MAP.get(ext)
        if not analyzer_script:
            print(error_response(f"No analyzer available for extension: {ext}"))
            return 1

        script_path = os.path.join(os.path.dirname(__file__), analyzer_script)
        debug(f"Using analyzer: {script_path}")

        result = run_analyzer(script_path, file_path)
        print(result)
        debug("=== Analysis Complete ===")
        return 0

    except Exception as e:
        print(error_response(f"Unexpected error: {str(e)}", traceback=traceback.format_exc()))
        return 1

if __name__ == "__main__":
    sys.exit(main())
