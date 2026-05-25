from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def _load_resume_utils():
    try:
        from utils.pdf_parser import extract_text_from_pdf
        from utils.resume_parser import parse_resume

        return extract_text_from_pdf, parse_resume, None
    except Exception as exc:
        logging.exception("Resume utilities unavailable")
        return None, None, str(exc)


def home(request):
    return render(request, 'career_advisor/home.html')


def upload_resume(request):
    if request.method == 'POST':

        if 'resume' in request.FILES:
            resume_file = request.FILES['resume']

            file_path = os.path.join(
                settings.MEDIA_ROOT,
                'resumes',
                resume_file.name
            )

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'wb+') as destination:
                for chunk in resume_file.chunks():
                    destination.write(chunk)

            try:
                extract_text_from_pdf, parse_resume, import_error = _load_resume_utils()

                if import_error:
                    raise RuntimeError(import_error)

                raw_text = extract_text_from_pdf(file_path)
                parsed_data = parse_resume(raw_text)

                request.session['resume_data'] = parsed_data
                request.session['resume_file'] = file_path

                messages.success(request, 'Resume uploaded successfully!')
                return redirect('career_advisor:analyze_resume')

            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
                return redirect('career_advisor:home')

        else:
            messages.error(request, 'No resume uploaded')
            return redirect('career_advisor:home')

    return render(request, 'career_advisor/upload.html')


def analyze_resume(request):

    resume_data = request.session.get('resume_data')

    if not resume_data:
        messages.warning(request, 'Please upload resume first')
        return redirect('career_advisor:home')

    context = {
        'resume_data': resume_data,
        'skills_count': len(resume_data.get('skills', [])),
        'projects_count': len(resume_data.get('projects', [])),
        'education_count': len(resume_data.get('education', [])),
        'experience_count': len(resume_data.get('experience', [])),
        'rag_available': False,
        'cache_info': {},
    }

    return render(request, 'career_advisor/analyze.html', context)


def skills_gap_analysis(request):

    resume_data = request.session.get('resume_data')

    if not resume_data:
        messages.warning(request, 'Please upload resume first')
        return redirect('career_advisor:home')

    if request.method == 'POST':

        target_role = request.POST.get('target_role', 'Data Scientist')

        analysis = analyze_skills_gap_fallback(
            resume_data,
            target_role
        )

        context = {
            'resume_data': resume_data,
            'analysis': analysis,
            'target_role': target_role,
            'rag_used': False,
        }

        return render(request, 'career_advisor/skills_gap.html', context)

    return render(
        request,
        'career_advisor/skills_gap_form.html',
        {'resume_data': resume_data}
    )


def career_paths(request):

    resume_data = request.session.get('resume_data')

    if not resume_data:
        messages.warning(request, 'Please upload resume first')
        return redirect('career_advisor:home')

    career_paths = suggest_career_paths(resume_data)

    context = {
        'resume_data': resume_data,
        'career_paths': career_paths,
        'rag_available': False,
    }

    return render(request, 'career_advisor/career_paths.html', context)


def career_chat(request):

    resume_data = request.session.get('resume_data')

    if not resume_data:
        messages.warning(request, 'Please upload resume first')
        return redirect('career_advisor:home')

    if request.method == 'POST':

        question = request.POST.get('question', '')

        answer = get_career_advice_fallback(question, resume_data)

        return JsonResponse({
            'answer': answer,
            'rag_used': False
        })

    return render(
        request,
        'career_advisor/chat.html',
        {
            'resume_data': resume_data,
            'rag_available': False,
        }
    )


def learning_roadmap(request):

    resume_data = request.session.get('resume_data')

    if not resume_data:
        messages.warning(request, 'Please upload resume first')
        return redirect('career_advisor:home')

    roadmap = generate_learning_roadmap(resume_data)

    context = {
        'resume_data': resume_data,
        'roadmap': roadmap,
        'rag_available': False,
    }

    return render(request, 'career_advisor/roadmap.html', context)


def performance_status(request):

    context = {
        'cache_info': {},
        'rag_available': False,
    }

    return render(request, 'career_advisor/performance.html', context)


def analyze_skills_gap_fallback(resume_data, target_role):

    role_skills = {
        "data scientist": [
            "Python",
            "SQL",
            "Machine Learning",
            "Statistics"
        ],
        "software engineer": [
            "Programming",
            "Algorithms",
            "Testing"
        ],
    }

    target_skills = role_skills.get(target_role.lower(), [])

    current_skills = set(resume_data.get("skills", []))

    missing_skills = [
        skill for skill in target_skills
        if skill.lower() not in current_skills
    ]

    return {
        "target_role": target_role,
        "current_skills": list(current_skills),
        "missing_skills": missing_skills,
    }


def suggest_career_paths(resume_data):

    skills = set(resume_data.get("skills", []))

    career_paths = []

    if any("python" in skill.lower() for skill in skills):
        career_paths.append("Data Scientist")
        career_paths.append("Software Engineer")

    if any("sql" in skill.lower() for skill in skills):
        career_paths.append("Data Analyst")

    return career_paths or ["Software Developer"]


def get_career_advice_fallback(question, resume_data):

    return "Keep improving your skills and building projects."


def generate_learning_roadmap(resume_data):

    return {
        "general": [
            "Build projects",
            "Practice DSA",
            "Learn deployment",
            "Contribute to GitHub"
        ]
    }