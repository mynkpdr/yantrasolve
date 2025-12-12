"""Tests for app/tools/python.py"""

import sys


from app.tools.python import python_tool, reset_python_session, GLOBAL_SCOPE


class TestPythonTool:
    """Test cases for python_tool function."""

    def setup_method(self):
        """Reset Python session before each test."""
        reset_python_session()

    def test_simple_print(self):
        """Test simple print statement."""
        result = python_tool.invoke({"code": "print('Hello, World!')"})
        assert result == "Hello, World!"

    def test_arithmetic_calculation(self):
        """Test arithmetic calculations."""
        result = python_tool.invoke({"code": "print(2 + 2)"})
        assert result == "4"

    def test_variable_assignment_and_use(self):
        """Test variable assignment persists across calls."""
        python_tool.invoke({"code": "x = 10"})
        result = python_tool.invoke({"code": "print(x * 2)"})
        assert result == "20"

    def test_pandas_available(self):
        """Test that pandas is pre-imported."""
        result = python_tool.invoke({"code": "print(pd.__name__)"})
        assert result == "pandas"

    def test_numpy_available(self):
        """Test that numpy is pre-imported."""
        result = python_tool.invoke({"code": "print(np.__name__)"})
        assert result == "numpy"

    def test_no_output_warning(self):
        """Test that no output returns a warning message."""
        result = python_tool.invoke({"code": "x = 5"})
        assert "No output provided" in result or "Did you forget to print" in result

    def test_syntax_error(self):
        """Test handling of syntax errors."""
        result = python_tool.invoke({"code": "if True print('error')"})
        assert "Error" in result or "error" in result.lower()

    def test_name_error_with_hint(self):
        """Test NameError includes helpful hint."""
        reset_python_session()
        result = python_tool.invoke({"code": "print(undefined_variable)"})
        assert "NameError" in result
        assert "Hint" in result

    def test_module_not_found_with_hint(self):
        """Test ModuleNotFoundError includes helpful hint."""
        result = python_tool.invoke({"code": "import nonexistent_module_xyz"})
        assert "ModuleNotFoundError" in result
        assert "Hint" in result

    def test_multiline_code(self):
        """Test multiline code execution."""
        code = """
for i in range(3):
    print(i)
"""
        result = python_tool.invoke({"code": code})
        assert "0" in result
        assert "1" in result
        assert "2" in result

    def test_function_definition_and_call(self):
        """Test function definition persists."""
        python_tool.invoke({"code": "def square(n): return n * n"})
        result = python_tool.invoke({"code": "print(square(5))"})
        assert result == "25"

    def test_list_comprehension(self):
        """Test list comprehension."""
        result = python_tool.invoke({"code": "print([x**2 for x in range(5)])"})
        assert "[0, 1, 4, 9, 16]" in result

    def test_pandas_operations(self):
        """Test pandas operations work."""
        code = """
df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
print(df['a'].sum())
"""
        result = python_tool.invoke({"code": code})
        assert "6" in result

    def test_numpy_operations(self):
        """Test numpy operations work."""
        code = """
arr = np.array([1, 2, 3, 4, 5])
print(np.mean(arr))
"""
        result = python_tool.invoke({"code": code})
        assert "3.0" in result

    def test_exception_traceback(self):
        """Test that exceptions include traceback."""
        result = python_tool.invoke({"code": "1 / 0"})
        assert "ZeroDivisionError" in result

    def test_stdout_captured(self):
        """Test that stdout is properly captured and restored."""
        original_stdout = sys.stdout
        python_tool.invoke({"code": "print('test')"})
        assert sys.stdout == original_stdout


class TestResetPythonSession:
    """Test cases for reset_python_session function."""

    def test_reset_clears_variables(self):
        """Test that reset clears user-defined variables."""
        python_tool.invoke({"code": "test_var = 123"})
        reset_python_session()
        result = python_tool.invoke({"code": "print(test_var)"})
        assert "NameError" in result

    def test_reset_preserves_pandas(self):
        """Test that reset preserves pandas import."""
        reset_python_session()
        result = python_tool.invoke({"code": "print(pd.__name__)"})
        assert result == "pandas"

    def test_reset_preserves_numpy(self):
        """Test that reset preserves numpy import."""
        reset_python_session()
        result = python_tool.invoke({"code": "print(np.__name__)"})
        assert result == "numpy"

    def test_reset_preserves_builtins(self):
        """Test that reset preserves builtins."""
        reset_python_session()
        result = python_tool.invoke({"code": "print(len([1, 2, 3]))"})
        assert result == "3"

    def test_global_scope_structure(self):
        """Test GLOBAL_SCOPE has expected structure after reset."""
        reset_python_session()

        assert "pd" in GLOBAL_SCOPE
        assert "np" in GLOBAL_SCOPE
        assert "__builtins__" in GLOBAL_SCOPE
