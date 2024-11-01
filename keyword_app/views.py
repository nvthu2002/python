# keyword_app/views.py
from django.shortcuts import render, redirect
import http.client
import json
import pandas as pd
import os
from .forms import KeywordForm
from django.core.exceptions import ValidationError
import tempfile

API_KEY = '9004a4e586f5f59e325a2e58efe4dba802c1fa61'

def google_search(query):
    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({"q": query})
    headers = {'X-API-KEY': API_KEY, 'Content-Type': 'application/json'}
    conn.request("POST", "/search", payload, headers)
    res = conn.getresponse()
    data = res.read()
    results = json.loads(data.decode("utf-8"))
    titles = [item['title'] for item in results.get('organic', [])[:3]]
    return titles

def calculate_similarity(list1, list2):
    intersection = len(set(list1) & set(list2))
    union = len(set(list1) | set(list2))
    return intersection / union if union else 0

def group_keywords(keywords):
    keyword_groups = {}
    search_results_cache = {}

    for keyword in keywords:
        search_results = google_search(keyword)
        search_results_cache[keyword] = search_results
        found_group = False

        for group_id, group_keywords in keyword_groups.items():
            existing_keyword = group_keywords[0]
            existing_search_results = search_results_cache[existing_keyword]

            similarity = calculate_similarity(search_results, existing_search_results)
            if similarity >= 0.5:
                keyword_groups[group_id].append(keyword)
                found_group = True
                break

        if not found_group:
            keyword_groups[keyword] = [keyword]

    keyword_list = []
    group_id_list = []
    for group_id, keywords in keyword_groups.items():
        for keyword in keywords:
            keyword_list.append(keyword)
            group_id_list.append(group_id)
    
    return pd.DataFrame({'keyword': keyword_list, 'group_id': group_id_list})

# keyword_app/views.py
def upload_file(request):
    if request.method == 'POST':
        form = KeywordForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            output_filename = form.cleaned_data['output_filename']

            # Kiểm tra phần mở rộng file
            if not file.name.endswith(('.xlsx', '.xls')):
                form.add_error('file', 'File phải có định dạng .xlsx hoặc .xls')
                return render(request, 'upload.html', {'form': form})

            # Tạo file tạm để đọc dữ liệu
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx" if file.name.endswith(".xlsx") else ".xls") as temp_file:
                    temp_file.write(file.read())
                    temp_file.flush()
                    temp_file_name = temp_file.name
                
                # Sử dụng tên file tạm để đọc vào pandas
                if temp_file_name.endswith('.xlsx'):
                    df = pd.read_excel(temp_file_name, engine='openpyxl')
                elif temp_file_name.endswith('.xls'):
                    df = pd.read_excel(temp_file_name, engine='xlrd')
                else:
                    raise ValueError("Định dạng file không hợp lệ.")
            except ValueError as e:
                form.add_error('file', 'Không thể đọc file: {}'.format(e))
                return render(request, 'upload.html', {'form': form})

            keywords = df['keyword'].tolist()
            result_df = group_keywords(keywords)

            output_path = f"{output_filename}.xlsx"  # Ensure .xlsx extension
            result_df.to_excel(output_path, index=False, engine='openpyxl')

            return render(request, 'result.html', {'output_path': output_path})
    else:
        form = KeywordForm()

    return render(request, 'upload.html', {'form': form})

def result_view(request):
    return render(request, 'result.html')
