from sqlalchemy.orm import Session
from .models import Student, StudentPerformance, QuizResult, LearningContent, Assignment
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, db: Session):
        self.db = db
    
    # Student operations
    def create_student(self, username: str, email: str, password_hash: str) -> Student:
        try:
            # Check if email already exists
            existing_email = self.db.query(Student).filter(Student.email == email).first()
            if existing_email:
                raise ValueError("Email already exists")
            
            student = Student(username=username, email=email, password_hash=password_hash)
            self.db.add(student)
            self.db.commit()
            self.db.refresh(student)
            return student
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_student_by_username(self, username: str) -> Optional[Student]:
        try:
            return self.db.query(Student).filter(Student.username == username).first()
        except Exception as e:
            self.db.rollback()
            return None
    
    def get_student_by_email(self, email: str) -> Optional[Student]:
        try:
            return self.db.query(Student).filter(Student.email == email).first()
        except Exception as e:
            self.db.rollback()
            return None
    
    def get_student_by_id(self, student_id: int) -> Optional[Student]:
        return self.db.query(Student).filter(Student.id == student_id).first()
    
    def update_student_stage(self, student_id: int, new_stage: int):
        student = self.get_student_by_id(student_id)
        if student:
            student.current_stage = new_stage
            self.db.commit()
    
    # Performance tracking
    def record_performance(self, student_id: int, topic: str, score: float, 
                         stage: int, difficulty_level: str, weak_topics: List[str] = None):
        performance = StudentPerformance(
            student_id=student_id,
            topic=topic,
            score=score,
            stage=stage,
            difficulty_level=difficulty_level,
            weak_topics=json.dumps(weak_topics) if weak_topics else None
        )
        self.db.add(performance)
        self.db.commit()
        self.db.refresh(performance)
        return performance
    
    def get_student_performance(self, student_id: int, topic: str = None) -> List[StudentPerformance]:
        query = self.db.query(StudentPerformance).filter(StudentPerformance.student_id == student_id)
        if topic:
            query = query.filter(StudentPerformance.topic == topic)
        return query.order_by(StudentPerformance.created_at.desc()).all()
    
    def get_weak_topics(self, student_id: int) -> List[str]:
        performances = self.get_student_performance(student_id)
        weak_topics = []
        for perf in performances:
            if perf.weak_topics:
                weak_topics.extend(json.loads(perf.weak_topics))
        return list(set(weak_topics))
    
    # Quiz operations
    def save_quiz_result(self, student_id: int, topic: str, questions: List[Dict],
                        answers: List[str], correct_answers: List[str], score: float, time_taken: int):
        quiz_result = QuizResult(
            student_id=student_id,
            topic=topic,
            questions=json.dumps(questions),
            answers=json.dumps(answers),
            correct_answers=json.dumps(correct_answers),
            score=score,
            time_taken=time_taken
        )
        self.db.add(quiz_result)
        self.db.commit()
        self.db.refresh(quiz_result)
        return quiz_result
    
    def get_quiz_results(self, student_id: int, topic: str = None) -> List[QuizResult]:
        query = self.db.query(QuizResult).filter(QuizResult.student_id == student_id)
        if topic:
            query = query.filter(QuizResult.topic == topic)
        return query.order_by(QuizResult.created_at.desc()).all()
    
    # Learning content operations
    def save_learning_content(self, topic: str, difficulty_level: str, 
                            content: str, key_concepts: List[str]):
        learning_content = LearningContent(
            topic=topic,
            difficulty_level=difficulty_level,
            content=content,
            key_concepts=json.dumps(key_concepts)
        )
        self.db.add(learning_content)
        self.db.commit()
        self.db.refresh(learning_content)
        return learning_content
    
    def get_learning_content(self, topic: str, difficulty_level: str) -> Optional[LearningContent]:
        return self.db.query(LearningContent).filter(
            LearningContent.topic == topic,
            LearningContent.difficulty_level == difficulty_level
        ).first()
    
    # Assignment operations
    def create_assignment(self, student_id: int, topic: str, difficulty_level: str, assignment_text: str):
        assignment = Assignment(
            student_id=student_id,
            topic=topic,
            difficulty_level=difficulty_level,
            assignment_text=assignment_text
        )
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment
    
    def get_student_assignments(self, student_id: int, topic: str = None) -> List[Assignment]:
        query = self.db.query(Assignment).filter(Assignment.student_id == student_id)
        if topic:
            query = query.filter(Assignment.topic == topic)
        return query.order_by(Assignment.created_at.desc()).all()
    
    def complete_assignment(self, assignment_id: int, score: float):
        assignment = self.db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if assignment:
            assignment.completed = True
            assignment.score = score
            assignment.completed_at = datetime.utcnow()
            self.db.commit()
        return assignment
    
    # Analytics
    def get_student_analytics(self, student_id: int) -> Dict[str, Any]:
        performances = self.get_student_performance(student_id)
        quiz_results = self.get_quiz_results(student_id)
        assignments = self.get_student_assignments(student_id)
        
        # Calculate average scores
        avg_performance_score = sum(p.score for p in performances) / len(performances) if performances else 0
        avg_quiz_score = sum(q.score for q in quiz_results) / len(quiz_results) if quiz_results else 0
        avg_assignment_score = sum(a.score for a in assignments if a.score) / len([a for a in assignments if a.score]) if assignments else 0
        
        # Topic-wise performance
        topic_performance = {}
        for perf in performances:
            if perf.topic not in topic_performance:
                topic_performance[perf.topic] = []
            topic_performance[perf.topic].append(perf.score)
        
        topic_averages = {topic: sum(scores) / len(scores) for topic, scores in topic_performance.items()}
        
        return {
            'total_topics': len(topic_performance),
            'average_performance_score': avg_performance_score,
            'average_quiz_score': avg_quiz_score,
            'average_assignment_score': avg_assignment_score,
            'topic_averages': topic_averages,
            'weak_topics': self.get_weak_topics(student_id),
            'total_quizzes_taken': len(quiz_results),
            'total_assignments_completed': len([a for a in assignments if a.completed])
        }
