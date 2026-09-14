"""
Data processing module for student records.
"""
from typing import List, Dict, Any, Optional

def process_student_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter and transform student records.
    Only includes active students and calculates their final grades.
    """
    processed = []
    for record in records:
        if not _is_active(record):
            continue
            
        final_grade = _calculate_final_grade(
            record.get('midterm', 0),
            record.get('final', 0),
            record.get('assignments', [])
        )
        
        processed.append({
            'student_id': record.get('id'),
            'name': record.get('name'),
            'final_grade': final_grade,
            'status': 'passed' if final_grade >= 60 else 'failed'
        })
    return processed

def _is_active(record: Dict[str, Any]) -> bool:
    """Check if the student record indicates active status."""
    return record.get('status', '').lower() == 'active'

def _calculate_final_grade(midterm: float, final: float, assignments: List[float]) -> float:
    """Calculate final grade based on weights."""
    assignment_avg = sum(assignments) / len(assignments) if assignments else 0.0
    return (midterm * 0.3) + (final * 0.5) + (assignment_avg * 0.2)
