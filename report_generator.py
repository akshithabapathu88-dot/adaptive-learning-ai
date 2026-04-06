from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import json
from typing import Dict, Any, List

class PDFReportGenerator:
    def __init__(self, output_dir: str = "./reports"):
        """
        Initialize the PDF Report Generator.
        
        Args:
            output_dir: Directory to save PDF reports
        """
        self.output_dir = output_dir
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the PDF."""
        # Custom title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.darkblue,
            borderPadding=10
        )
        
        # Custom heading style
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue,
            borderWidth=0,
            borderBottomWidth=1,
            borderBottomColor=colors.grey,
            borderBottomPadding=5
        )
        
        # Custom subheading style
        self.subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=15,
            textColor=colors.darkgreen
        )
        
        # Custom body style
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            leftIndent=20
        )
        
        # Custom list style
        self.list_style = ParagraphStyle(
            'CustomList',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            leftIndent=40,
            bulletIndent=20
        )
    
    def generate_student_report(self, report_data: Dict[str, Any]) -> str:
        """
        Generate a comprehensive student learning report.
        
        Args:
            report_data: Dictionary containing all report data including:
                - student_info: Student information
                - learning_content: Generated learning content
                - assignments: Generated assignments
                - quiz_results: Quiz results and analysis
                - recommendations: Learning recommendations
                - performance_analytics: Performance analytics
                
        Returns:
            Path to generated PDF file
        """
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        student_name = report_data.get('student_info', {}).get('username', 'student')
        filename = f"learning_report_{student_name}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4, 
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Build story (content)
        story = []
        
        # Title page
        story.extend(self._create_title_page(report_data))
        story.append(PageBreak())
        
        # Table of contents
        story.extend(self._create_table_of_contents())
        story.append(PageBreak())
        
        # Student Information
        story.extend(self._create_student_info_section(report_data.get('student_info', {})))
        
        # Learning Content
        story.extend(self._create_learning_content_section(report_data.get('learning_content', {})))
        
        # Assignments
        story.extend(self._create_assignments_section(report_data.get('assignments', {})))
        
        # Quiz Results
        story.extend(self._create_quiz_results_section(report_data.get('quiz_results', {})))
        
        # Performance Analytics
        story.extend(self._create_performance_analytics_section(report_data.get('performance_analytics', {})))
        
        # Recommendations
        story.extend(self._create_recommendations_section(report_data.get('recommendations', {})))
        
        # Summary and Next Steps
        story.extend(self._create_summary_section(report_data))
        
        # Build PDF
        doc.build(story)
        
        return filepath
    
    def _create_title_page(self, report_data: Dict[str, Any]) -> List:
        """Create the title page of the report."""
        elements = []
        
        # Add spacing
        elements.append(Spacer(1, 2*inch))
        
        # Main title
        title = Paragraph("AI-Based Personalized Learning Report", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # Subtitle
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=30
        )
        subtitle = Paragraph("Adaptive Student Learning System", subtitle_style)
        elements.append(subtitle)
        elements.append(Spacer(1, 1*inch))
        
        # Student information
        student_info = report_data.get('student_info', {})
        info_style = ParagraphStyle(
            'Info',
            parent=self.styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=10
        )
        
        elements.append(Paragraph(f"Student: {student_info.get('username', 'N/A')}", info_style))
        elements.append(Paragraph(f"Topic: {report_data.get('topic', 'N/A')}", info_style))
        elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", info_style))
        elements.append(Paragraph(f"Report ID: {report_data.get('report_id', 'N/A')}", info_style))
        
        return elements
    
    def _create_table_of_contents(self) -> List:
        """Create table of contents."""
        elements = []
        
        elements.append(Paragraph("Table of Contents", self.title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        toc_items = [
            "1. Student Information",
            "2. Learning Content",
            "3. Assignments",
            "4. Quiz Results",
            "5. Performance Analytics",
            "6. Recommendations",
            "7. Summary and Next Steps"
        ]
        
        for item in toc_items:
            elements.append(Paragraph(item, self.body_style))
            elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _create_student_info_section(self, student_info: Dict[str, Any]) -> List:
        """Create student information section."""
        elements = []
        
        elements.append(Paragraph("1. Student Information", self.heading_style))
        
        # Create student info table
        data = [
            ['Field', 'Information'],
            ['Name', student_info.get('username', 'N/A')],
            ['Email', student_info.get('email', 'N/A')],
            ['Current Stage', str(student_info.get('current_stage', 'N/A'))],
            ['Registration Date', student_info.get('created_at', 'N/A')],
            ['Total Topics Studied', str(student_info.get('total_topics', 'N/A'))]
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_learning_content_section(self, learning_content: Dict[str, Any]) -> List:
        """Create learning content section."""
        elements = []
        
        elements.append(Paragraph("2. Learning Content", self.heading_style))
        
        if not learning_content:
            elements.append(Paragraph("No learning content available.", self.body_style))
            return elements
        
        # Topic information
        elements.append(Paragraph("Topic Information", self.subheading_style))
        elements.append(Paragraph(f"<b>Topic:</b> {learning_content.get('topic', 'N/A')}", self.body_style))
        elements.append(Paragraph(f"<b>Difficulty Level:</b> {learning_content.get('difficulty_level', 'N/A')}", self.body_style))
        elements.append(Paragraph(f"<b>Student Stage:</b> {learning_content.get('student_stage', 'N/A')}", self.body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Learning objectives
        objectives = learning_content.get('learning_objectives', [])
        if objectives:
            elements.append(Paragraph("Learning Objectives", self.subheading_style))
            for obj in objectives:
                elements.append(Paragraph(f"• {obj}", self.list_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Main content
        main_content = learning_content.get('content', '')
        if main_content:
            elements.append(Paragraph("Content Explanation", self.subheading_style))
            elements.append(Paragraph(main_content, self.body_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Key concepts
        key_concepts = learning_content.get('key_concepts', [])
        if key_concepts:
            elements.append(Paragraph("Key Concepts", self.subheading_style))
            for concept in key_concepts:
                elements.append(Paragraph(f"• {concept}", self.list_style))
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_assignments_section(self, assignments: Dict[str, Any]) -> List:
        """Create assignments section."""
        elements = []
        
        elements.append(Paragraph("3. Assignments", self.heading_style))
        
        if not assignments or not assignments.get('assignments'):
            elements.append(Paragraph("No assignments available.", self.body_style))
            return elements
        
        assignment_list = assignments.get('assignments', [])
        elements.append(Paragraph(f"Total Assignments: {len(assignment_list)}", self.body_style))
        elements.append(Paragraph(f"Estimated Completion Time: {assignments.get('estimated_completion_time', 'N/A')}", self.body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        for i, assignment in enumerate(assignment_list, 1):
            elements.append(Paragraph(f"Assignment {i}: {assignment.get('title', 'N/A')}", self.subheading_style))
            elements.append(Paragraph(f"<b>Type:</b> {assignment.get('type', 'N/A')}", self.body_style))
            elements.append(Paragraph(f"<b>Difficulty:</b> {assignment.get('difficulty', 'N/A')}", self.body_style))
            elements.append(Paragraph(f"<b>Estimated Time:</b> {assignment.get('estimated_time', 'N/A')}", self.body_style))
            
            description = assignment.get('description', '')
            if description:
                elements.append(Paragraph("<b>Description:</b>", self.body_style))
                elements.append(Paragraph(description, self.body_style))
            
            instructions = assignment.get('instructions', [])
            if instructions:
                elements.append(Paragraph("<b>Instructions:</b>", self.body_style))
                for j, instruction in enumerate(instructions, 1):
                    elements.append(Paragraph(f"{j}. {instruction}", self.list_style))
            
            deliverables = assignment.get('deliverables', [])
            if deliverables:
                elements.append(Paragraph("<b>Deliverables:</b>", self.body_style))
                for deliverable in deliverables:
                    elements.append(Paragraph(f"• {deliverable}", self.list_style))
            
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_quiz_results_section(self, quiz_results: Dict[str, Any]) -> List:
        """Create quiz results section."""
        elements = []
        
        elements.append(Paragraph("4. Quiz Results", self.heading_style))
        
        if not quiz_results:
            elements.append(Paragraph("No quiz results available.", self.body_style))
            return elements
        
        # Quiz summary
        elements.append(Paragraph("Quiz Summary", self.subheading_style))
        elements.append(Paragraph(f"<b>Topic:</b> {quiz_results.get('topic', 'N/A')}", self.body_style))
        elements.append(Paragraph(f"<b>Difficulty Level:</b> {quiz_results.get('difficulty_level', 'N/A')}", self.body_style))
        elements.append(Paragraph(f"<b>Total Questions:</b> {quiz_results.get('total_questions', 'N/A')}", self.body_style))
        elements.append(Paragraph(f"<b>Correct Answers:</b> {quiz_results.get('correct_answers', 'N/A')}", self.body_style))
        elements.append(Paragraph(f"<b>Score:</b> {quiz_results.get('score_percentage', 'N/A'):.1f}%", self.body_style))
        elements.append(Paragraph(f"<b>Grade:</b> {quiz_results.get('grade', 'N/A')}", self.body_style))
        elements.append(Paragraph(f"<b>Passed:</b> {'Yes' if quiz_results.get('passed', False) else 'No'}", self.body_style))
        elements.append(Paragraph(f"<b>Time Taken:</b> {quiz_results.get('time_taken', 'N/A')} seconds", self.body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Question analysis
        question_analysis = quiz_results.get('question_analysis', [])
        if question_analysis:
            elements.append(Paragraph("Question Analysis", self.subheading_style))
            
            # Create question analysis table
            data = [['Q#', 'Correct?', 'Topic Area', 'Difficulty']]
            for q in question_analysis:
                data.append([
                    str(q.get('question_id', 'N/A')),
                    'Yes' if q.get('is_correct', False) else 'No',
                    q.get('topic_area', 'N/A'),
                    q.get('difficulty', 'N/A')
                ])
            
            table = Table(data, colWidths=[0.5*inch, 0.8*inch, 2*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.2*inch))
        
        # Feedback
        feedback = quiz_results.get('detailed_feedback', '')
        if feedback:
            elements.append(Paragraph("Feedback", self.subheading_style))
            elements.append(Paragraph(feedback, self.body_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Strengths and improvement areas
        strengths = quiz_results.get('strengths', [])
        if strengths:
            elements.append(Paragraph("Strengths", self.subheading_style))
            for strength in strengths:
                elements.append(Paragraph(f"• {strength}", self.list_style))
            elements.append(Spacer(1, 0.1*inch))
        
        improvements = quiz_results.get('improvement_areas', [])
        if improvements:
            elements.append(Paragraph("Areas for Improvement", self.subheading_style))
            for improvement in improvements:
                elements.append(Paragraph(f"• {improvement}", self.list_style))
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_performance_analytics_section(self, performance_analytics: Dict[str, Any]) -> List:
        """Create performance analytics section."""
        elements = []
        
        elements.append(Paragraph("5. Performance Analytics", self.heading_style))
        
        if not performance_analytics:
            elements.append(Paragraph("No performance analytics available.", self.body_style))
            return elements
        
        # Overall metrics
        elements.append(Paragraph("Overall Performance", self.subheading_style))
        elements.append(Paragraph(f"<b>Total Topics Studied:</b> {performance_analytics.get('total_topics', 'N/A')}", self.body_style))
        elements.append(Paragraph(f"<b>Average Performance Score:</b> {performance_analytics.get('average_performance_score', 'N/A'):.1f}%", self.body_style))
        elements.append(Paragraph(f"<b>Average Quiz Score:</b> {performance_analytics.get('average_quiz_score', 'N/A'):.1f}%", self.body_style))
        elements.append(Paragraph(f"<b>Average Assignment Score:</b> {performance_analytics.get('average_assignment_score', 'N/A'):.1f}%", self.body_style))
        elements.append(Paragraph(f"<b>Total Quizzes Taken:</b> {performance_analytics.get('total_quizzes_taken', 'N/A')}", self.body_style))
        elements.append(Paragraph(f"<b>Total Assignments Completed:</b> {performance_analytics.get('total_assignments_completed', 'N/A')}", self.body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Topic-wise performance
        topic_averages = performance_analytics.get('topic_averages', {})
        if topic_averages:
            elements.append(Paragraph("Topic-wise Performance", self.subheading_style))
            
            data = [['Topic', 'Average Score']]
            for topic, score in topic_averages.items():
                data.append([topic, f"{score:.1f}%"])
            
            table = Table(data, colWidths=[3*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.2*inch))
        
        # Weak topics
        weak_topics = performance_analytics.get('weak_topics', [])
        if weak_topics:
            elements.append(Paragraph("Weak Topics", self.subheading_style))
            for topic in weak_topics:
                elements.append(Paragraph(f"• {topic}", self.list_style))
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_recommendations_section(self, recommendations: Dict[str, Any]) -> List:
        """Create recommendations section."""
        elements = []
        
        elements.append(Paragraph("6. Recommendations", self.heading_style))
        
        if not recommendations:
            elements.append(Paragraph("No recommendations available.", self.body_style))
            return elements
        
        # Learning path
        learning_path = recommendations.get('learning_path', {})
        if learning_path:
            elements.append(Paragraph("Learning Path", self.subheading_style))
            elements.append(Paragraph(f"<b>Current Focus:</b> {learning_path.get('current_focus', 'N/A')}", self.body_style))
            elements.append(Paragraph(f"<b>Progression Timeline:</b> {learning_path.get('progression_timeline', 'N/A')}", self.body_style))
            
            next_topics = learning_path.get('next_topics', [])
            if next_topics:
                elements.append(Paragraph("<b>Next Topics:</b>", self.body_style))
                for topic in next_topics:
                    elements.append(Paragraph(f"• {topic}", self.list_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Topic recommendations
        topic_recs = recommendations.get('topic_recommendations', [])
        if topic_recs:
            elements.append(Paragraph("Topic Recommendations", self.subheading_style))
            for rec in topic_recs:
                elements.append(Paragraph(f"<b>{rec.get('topic', 'N/A')}</b> (Priority: {rec.get('priority', 'N/A')})", self.body_style))
                elements.append(Paragraph(f"Reason: {rec.get('reason', 'N/A')}", self.body_style))
                elements.append(Paragraph(f"Estimated Duration: {rec.get('estimated_duration', 'N/A')}", self.body_style))
                elements.append(Spacer(1, 0.1*inch))
        
        # Study schedule
        study_schedule = recommendations.get('study_schedule', {})
        if study_schedule:
            elements.append(Paragraph("Study Schedule", self.subheading_style))
            
            weekly_structure = study_schedule.get('weekly_structure', [])
            if weekly_structure:
                elements.append(Paragraph("<b>Weekly Structure:</b>", self.body_style))
                for day in weekly_structure:
                    elements.append(Paragraph(f"<b>{day.get('day', 'N/A')}:</b> {day.get('focus', 'N/A')} ({day.get('duration', 'N/A')})", self.list_style))
            
            study_techniques = study_schedule.get('study_techniques', [])
            if study_techniques:
                elements.append(Paragraph("<b>Recommended Study Techniques:</b>", self.body_style))
                for technique in study_techniques:
                    elements.append(Paragraph(f"• {technique}", self.list_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # General recommendations
        general_recs = recommendations.get('recommendations', [])
        if general_recs:
            elements.append(Paragraph("General Recommendations", self.subheading_style))
            for rec in general_recs:
                elements.append(Paragraph(f"• {rec}", self.list_style))
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_summary_section(self, report_data: Dict[str, Any]) -> List:
        """Create summary and next steps section."""
        elements = []
        
        elements.append(Paragraph("7. Summary and Next Steps", self.heading_style))
        
        # Overall summary
        elements.append(Paragraph("Overall Summary", self.subheading_style))
        
        student_info = report_data.get('student_info', {})
        quiz_results = report_data.get('quiz_results', {})
        
        summary_text = f"""
        This report provides a comprehensive analysis of {student_info.get('username', 'the student')}'s learning progress 
        in {report_data.get('topic', 'the selected topic')}. The student has achieved a score of 
        {quiz_results.get('score_percentage', 0):.1f}% in the recent assessment, demonstrating 
        {'strong' if quiz_results.get('score_percentage', 0) >= 70 else 'developing'} understanding of the material.
        """
        
        elements.append(Paragraph(summary_text, self.body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Key achievements
        elements.append(Paragraph("Key Achievements", self.subheading_style))
        elements.append(Paragraph("• Completed personalized learning content", self.list_style))
        elements.append(Paragraph("• Successfully attempted challenging assignments", self.list_style))
        elements.append(Paragraph("• Demonstrated progress in assessed areas", self.list_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Next steps
        elements.append(Paragraph("Recommended Next Steps", self.subheading_style))
        elements.append(Paragraph("1. Review weak areas identified in the analysis", self.list_style))
        elements.append(Paragraph("2. Practice additional exercises in challenging topics", self.list_style))
        elements.append(Paragraph("3. Explore advanced topics once current concepts are mastered", self.list_style))
        elements.append(Paragraph("4. Schedule regular practice sessions to maintain momentum", self.list_style))
        elements.append(Paragraph("5. Seek additional help or resources when needed", self.list_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Contact information
        elements.append(Paragraph("Support and Contact", self.subheading_style))
        elements.append(Paragraph("For additional support or questions about this report, please contact your learning advisor.", self.body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Report generation info
        elements.append(Paragraph(f"Report generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", self.body_style))
        elements.append(Paragraph(f"Report ID: {report_data.get('report_id', 'N/A')}", self.body_style))
        
        return elements
    
    def generate_assignment_report(self, assignment_data: Dict[str, Any]) -> str:
        """
        Generate a standalone assignment report.
        
        Args:
            assignment_data: Assignment data including questions and student answers
            
        Returns:
            Path to generated PDF file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        student_name = assignment_data.get('student_id', 'student')
        filename = f"assignment_report_{student_name}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Title
        story.append(Paragraph("Assignment Report", self.title_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Assignment details
        story.append(Paragraph(f"Student: {assignment_data.get('student_id', 'N/A')}", self.body_style))
        story.append(Paragraph(f"Topic: {assignment_data.get('topic', 'N/A')}", self.body_style))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", self.body_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Questions and answers
        questions = assignment_data.get('questions', [])
        for i, question in enumerate(questions, 1):
            story.append(Paragraph(f"Question {i}", self.subheading_style))
            story.append(Paragraph(question.get('question', ''), self.body_style))
            
            student_answer = question.get('student_answer', 'Not answered')
            story.append(Paragraph(f"Your Answer: {student_answer}", self.body_style))
            
            correct_answer = question.get('correct_answer', 'N/A')
            story.append(Paragraph(f"Correct Answer: {correct_answer}", self.body_style))
            
            if question.get('explanation'):
                story.append(Paragraph(f"Explanation: {question.get('explanation', '')}", self.body_style))
            
            story.append(Spacer(1, 0.2*inch))
        
        doc.build(story)
        return filepath
