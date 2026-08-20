"""Tests for the CodePilot Language Detector.

Covers:
* All six supported languages correctly detected
* Language mismatches
* Filename extension support and conflict with code
* Ambiguous / empty / comments-only code
* Confidence boundaries
"""

from app.engine.language_detector import LanguageDetector


class TestLanguageDetector:
    def setup_method(self):
        self.detector = LanguageDetector()

    # -- Correct detection for each language --

    def test_detect_python(self):
        code = '''
import os
from pathlib import Path

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

class Calculator:
    def __init__(self):
        self.result = None

    def add(self, a, b):
        return a + b

print(factorial(5))
'''
        result = self.detector.detect(code)
        assert result.detected_language == "Python"
        assert result.confidence >= 75
        assert len(result.evidence) > 0

    def test_detect_java(self):
        code = '''
package com.example;

import java.util.ArrayList;

public class Main {
    public static void main(String[] args) {
        ArrayList<String> list = new ArrayList<>();
        list.add("Hello");
        System.out.println(list.get(0));
    }

    private int calculate(int x) {
        return x * 2;
    }
}
'''
        result = self.detector.detect(code)
        assert result.detected_language == "Java"
        assert result.confidence >= 75

    def test_detect_javascript(self):
        code = '''
const express = require('express');
const app = express();

function greet(name) {
    console.log(`Hello, ${name}!`);
}

app.get('/', (req, res) => {
    res.send('Hello World');
});

module.exports = app;

let count = 0;
if (count === 0) {
    console.warn('Count is zero');
}
'''
        result = self.detector.detect(code)
        assert result.detected_language == "JavaScript"
        assert result.confidence >= 75

    def test_detect_typescript(self):
        code = '''
interface User {
    id: number;
    name: string;
    email: string;
}

type Role = 'admin' | 'user' | 'guest';

enum Status {
    Active,
    Inactive,
}

export function getUser(id: number): User {
    const user: User = { id: 1, name: 'Test', email: 'test@test.com' };
    return user;
}

async function fetchData(): Promise<void> {
    const result = await fetch('/api');
    console.log(result);
}
'''
        result = self.detector.detect(code)
        assert result.detected_language == "TypeScript"
        assert result.confidence >= 75

    def test_detect_c(self):
        code = '''
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int x;
    int y;
} Point;

int main(int argc, char *argv[]) {
    Point *p = (Point *)malloc(sizeof(Point));
    p->x = 10;
    p->y = 20;
    printf("Point: (%d, %d)\\n", p->x, p->y);
    free(p);
    return 0;
}
'''
        result = self.detector.detect(code)
        assert result.detected_language == "C"
        assert result.confidence >= 75

    def test_detect_cpp(self):
        code = '''
#include <iostream>
#include <vector>

using namespace std;

namespace MyApp {
    class Calculator {
    public:
        virtual int add(int a, int b) { return a + b; }
    };
}

int main() {
    auto calc = new MyApp::Calculator();
    std::cout << calc->add(3, 4) << endl;
    delete calc;
    return 0;
}
'''
        result = self.detector.detect(code)
        assert result.detected_language == "C++"
        assert result.confidence >= 75

    # -- Mismatch detection --

    def test_python_submitted_as_java_mismatch(self):
        code = '''
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

for i in range(10):
    print(factorial(i))
'''
        validation = self.detector.validate_language("Java", code)
        assert validation["selected_language"] == "Java"
        assert validation["detected_language"] == "Python"
        assert validation["is_match"] is False
        assert validation["confidence"] >= 50

    def test_java_submitted_as_python_mismatch(self):
        code = '''
import java.util.List;

public class App {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
'''
        validation = self.detector.validate_language("Python", code)
        assert validation["selected_language"] == "Python"
        assert validation["detected_language"] == "Java"
        assert validation["is_match"] is False

    def test_correct_language_match(self):
        code = '''
def hello():
    print("Hello, World!")
'''
        validation = self.detector.validate_language("Python", code)
        assert validation["is_match"] is True

    # -- Filename extension tests --

    def test_filename_supports_correct_detection(self):
        code = '''
def hello():
    print("Hello")
'''
        result = self.detector.detect(code, filename="main.py")
        assert result.detected_language == "Python"
        # Confidence should be boosted by matching extension
        result_no_file = self.detector.detect(code, filename=None)
        assert result.confidence >= result_no_file.confidence

    def test_filename_conflicting_with_source(self):
        # Python code in a .java file — code evidence should win
        code = '''
import os
from pathlib import Path

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

class Calculator:
    def __init__(self):
        self.result = None

print(factorial(5))
'''
        result = self.detector.detect(code, filename="Test.java")
        assert result.detected_language == "Python"

    def test_filename_without_extension(self):
        code = '''
def hello():
    print("Hello")
'''
        result = self.detector.detect(code, filename="Makefile")
        assert result.detected_language == "Python"

    # -- Edge cases --

    def test_empty_code(self):
        result = self.detector.detect("")
        assert result.detected_language == "Unknown"
        assert result.confidence == 0

    def test_whitespace_only(self):
        result = self.detector.detect("   \n\n   \t  ")
        assert result.detected_language == "Unknown"
        assert result.confidence == 0

    def test_comments_only(self):
        code = '''
# This is just a comment
# Another comment line
# No actual code here
'''
        result = self.detector.detect(code)
        assert result.detected_language == "Unknown"
        assert result.confidence <= 20

    def test_very_short_code(self):
        # Very short code should have lower confidence
        code = "x = 5"
        result = self.detector.detect(code)
        # Could be detected or unknown, but confidence should be low
        assert result.confidence < 90

    def test_ambiguous_code(self):
        # Code that could be multiple languages
        code = "int x = 5;"
        result = self.detector.detect(code)
        # Should still detect something, but with lower confidence
        assert result.confidence < 90

    # -- Confidence boundaries --

    def test_confidence_never_exceeds_100(self):
        # Throw a ton of Python fingerprints
        code = '''
import os
import sys
from pathlib import Path
from collections import defaultdict

def foo():
    pass

def bar():
    pass

def baz():
    pass

class MyClass:
    def __init__(self):
        self.x = None
        self.y = True
        self.z = False

    def __repr__(self):
        return "MyClass"

    def method(self):
        for i in range(10):
            print(i)
        if True:
            pass
        elif False:
            pass
        raise ValueError("test")

@decorator
def decorated():
    lambda x: x + 1
'''
        result = self.detector.detect(code)
        assert result.confidence <= 100

    def test_confidence_never_below_0(self):
        result = self.detector.detect("")
        assert result.confidence >= 0

    # -- DetectionResult serialization --

    def test_to_dict(self):
        result = self.detector.detect("def hello(): pass")
        d = result.to_dict()
        assert "detected_language" in d
        assert "confidence" in d
        assert "evidence" in d
        assert isinstance(d["evidence"], list)

    # -- Validate_language with Unknown detection --

    def test_unknown_detection_counts_as_match(self):
        # When we can't detect, we don't flag mismatch
        validation = self.detector.validate_language("Python", "")
        assert validation["is_match"] is True  # Unknown => don't flag
