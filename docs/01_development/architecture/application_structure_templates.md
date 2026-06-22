# Flaskアプリケーション構成案 - HTMLテンプレート

## 5. HTMLテンプレート構成

### 5.1 app/templates/base.html（ベーステンプレート）

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}ワークフロー申請システム{% endblock %}</title>
    
    <!-- CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- ヘッダー -->
    {% include 'layout/header.html' %}
    
    <div class="container">
        <!-- サイドバー -->
        <aside class="sidebar">
            {% include 'layout/sidebar.html' %}
        </aside>
        
        <!-- メインコンテンツ -->
        <main class="main-content">
            <!-- パンくずリスト -->
            {% include 'layout/breadcrumb.html' %}
            
            <!-- フラッシュメッセージ -->
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <div class="flash-messages">
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">
                                {{ message }}
                            </div>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}
            
            <!-- ページタイトル -->
            <h1 class="page-title">{% block page_title %}{% endblock %}</h1>
            
            <!-- コンテンツ -->
            {% block content %}{% endblock %}
        </main>
    </div>
    
    <!-- フッター -->
    {% include 'layout/footer.html' %}
    
    <!-- JavaScript -->
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

---

### 5.2 app/templates/layout/header.html

```html
<header class="header">
    <div class="header-container">
        <div class="header-logo">
            <a href="{{ url_for('application.index') }}">
                <h1>ワークフロー申請システム</h1>
            </a>
        </div>
        
        <nav class="header-nav">
            <ul>
                <li><a href="{{ url_for('application.index') }}">新規申請</a></li>
                <li><a href="{{ url_for('application.list') }}">申請一覧</a></li>
                <li><a href="{{ url_for('approval.task_list') }}">承認待ちタスク</a></li>
                {% if session.is_admin %}
                <li><a href="{{ url_for('admin.dashboard') }}">管理画面</a></li>
                {% endif %}
            </ul>
        </nav>
        
        <div class="header-user">
            <span class="user-name">{{ session.user_name }}</span>
            <span class="user-shozoku">({{ session.shozoku_name }})</span>
            <a href="{{ url_for('auth.logout') }}" class="btn-logout">ログアウト</a>
        </div>
    </div>
</header>
```

---

### 5.3 app/templates/layout/sidebar.html

```html
<div class="sidebar-menu">
    <h3>メニュー</h3>
    <ul>
        <li class="menu-section">
            <span class="menu-title">申請</span>
            <ul class="submenu">
                <li><a href="{{ url_for('application.index') }}">新規申請作成</a></li>
                <li><a href="{{ url_for('application.list') }}">申請一覧</a></li>
                <li><a href="{{ url_for('application.list', status='draft') }}">下書き一覧</a></li>
            </ul>
        </li>
        
        <li class="menu-section">
            <span class="menu-title">承認</span>
            <ul class="submenu">
                <li>
                    <a href="{{ url_for('approval.task_list') }}">
                        承認待ちタスク
                        {% if pending_count > 0 %}
                        <span class="badge">{{ pending_count }}</span>
                        {% endif %}
                    </a>
                </li>
                <li><a href="{{ url_for('approval.approved_list') }}">承認済み一覧</a></li>
                <li><a href="{{ url_for('approval.history') }}">承認履歴</a></li>
            </ul>
        </li>
        
        {% if session.is_admin %}
        <li class="menu-section">
            <span class="menu-title">管理</span>
            <ul class="submenu">
                <li><a href="{{ url_for('admin.dashboard') }}">ダッシュボード</a></li>
                <li><a href="{{ url_for('admin.application_type') }}">申請種類管理</a></li>
                <li><a href="{{ url_for('admin.workflow_definition') }}">ワークフロー管理</a></li>
                <li><a href="{{ url_for('admin.resource_sync') }}">リソース同期</a></li>
            </ul>
        </li>
        {% endif %}
    </ul>
</div>
```

---

### 5.4 app/templates/application/index.html（申請種類選択）

```html
{% extends 'base.html' %}

{% block title %}申請種類選択 - ワークフロー申請システム{% endblock %}
{% block page_title %}新規申請作成{% endblock %}

{% block content %}
<div class="application-type-selection">
    <p class="description">作成する申請の種類を選択してください。</p>
    
    <div class="application-type-grid">
        {% for app_type in application_types %}
        <div class="application-type-card">
            <h3>{{ app_type.application_type_name }}</h3>
            <p class="description">{{ app_type.description }}</p>
            
            <div class="action-buttons">
                {% if app_type.support_create == 'Y' %}
                <a href="{{ url_for('application.create', application_type_id=app_type.application_type_id) }}" 
                   class="btn btn-primary">新規作成</a>
                {% endif %}
                
                {% if app_type.support_modify == 'Y' %}
                <a href="{{ url_for('application.modify', application_type_id=app_type.application_type_id) }}" 
                   class="btn btn-secondary">修正</a>
                {% endif %}
                
                {% if app_type.support_delete == 'Y' %}
                <a href="{{ url_for('application.delete', application_type_id=app_type.application_type_id) }}" 
                   class="btn btn-danger">削除</a>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

---

### 5.5 app/templates/application/create.html（新規申請作成）

```html
{% extends 'base.html' %}

{% block title %}{{ app_type.application_type_name }} - 新規作成{% endblock %}
{% block page_title %}{{ app_type.application_type_name }} - 新規作成{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/application.css') }}">
{% endblock %}

{% block content %}
<div class="application-form">
    <form method="POST" action="{{ url_for('application.create_submit', application_type_id=app_type.application_type_id) }}" 
          id="applicationForm">
        
        <!-- 基本情報 -->
        <section class="form-section">
            <h2>基本情報</h2>
            
            <div class="form-group">
                <label for="application_title" class="required">申請タイトル</label>
                <input type="text" id="application_title" name="application_title" 
                       class="form-control" required maxlength="200">
            </div>
            
            {% if app_type.has_target_user == 'Y' %}
            <div class="form-group">
                <label for="target_user_id" class="required">申請対象ユーザー</label>
                <select id="target_user_id" name="target_user_id" class="form-control" required>
                    <option value="">選択してください</option>
                    <!-- 同一所属のユーザーを取得して表示 -->
                </select>
            </div>
            {% endif %}
            
            {% if app_type.requires_jurisdiction == 'Y' and app_type.jurisdiction_restriction != 'jurisdiction_only' %}
            <div class="form-group">
                <label for="jurisdiction_shozoku">所管所属</label>
                <input type="text" id="jurisdiction_shozoku" name="jurisdiction_shozoku" 
                       class="form-control" readonly>
                <span class="help-text">リソース選択時に自動設定されます</span>
            </div>
            {% endif %}
        </section>
        
        <!-- 申請詳細フィールド -->
        <section class="form-section">
            <h2>申請内容</h2>
            
            {% for field in fields %}
            <div class="form-group">
                <label for="field_{{ field.field_id }}" 
                       {% if field.is_required %}class="required"{% endif %}>
                    {{ field.field_name }}
                </label>
                
                {% if field.field_type == 'text' %}
                <input type="text" 
                       id="field_{{ field.field_id }}" 
                       name="field_{{ field.field_id }}" 
                       class="form-control"
                       {% if field.is_required %}required{% endif %}
                       placeholder="{{ field.placeholder }}">
                
                {% elif field.field_type == 'number' %}
                <input type="number" 
                       id="field_{{ field.field_id }}" 
                       name="field_{{ field.field_id }}" 
                       class="form-control"
                       {% if field.is_required %}required{% endif %}>
                
                {% elif field.field_type == 'date' %}
                <input type="date" 
                       id="field_{{ field.field_id }}" 
                       name="field_{{ field.field_id }}" 
                       class="form-control"
                       {% if field.is_required %}required{% endif %}>
                
                {% elif field.field_type == 'select' %}
                <select id="field_{{ field.field_id }}" 
                        name="field_{{ field.field_id }}" 
                        class="form-control"
                        {% if field.is_required %}required{% endif %}>
                    <option value="">選択してください</option>
                    <!-- プルダウン選択肢を動的に読み込み -->
                </select>
                
                {% elif field.field_type == 'textarea' %}
                <textarea id="field_{{ field.field_id }}" 
                          name="field_{{ field.field_id }}" 
                          class="form-control" 
                          rows="5"
                          {% if field.is_required %}required{% endif %}
                          placeholder="{{ field.placeholder }}"></textarea>
                
                {% elif field.field_type == 'checkbox' %}
                <div style="padding: 0.5rem 0;">
                    <label style="display: inline-flex; align-items: center; font-weight: normal; cursor: pointer;">
                        <input type="checkbox"
                               id="field_{{ field.field_id }}"
                               name="field_{{ field.field_id }}"
                               value="Y"
                               {% if field.default_value == 'Y' %}checked{% endif %}
                               style="width: auto; margin-right: 0.5rem;">
                        {{ field.field_name }}
                    </label>
                </div>
                {% endif %}
                
                {% if field.help_text %}
                <span class="help-text">{{ field.help_text }}</span>
                {% endif %}
            </div>
            {% endfor %}
        </section>
        
        <!-- 備考 -->
        <section class="form-section">
            <h2>備考</h2>
            
            <div class="form-group">
                <label for="remarks">備考</label>
                <textarea id="remarks" name="remarks" class="form-control" rows="5"></textarea>
            </div>
        </section>
        
        <!-- アクションボタン -->
        <div class="form-actions">
            <button type="submit" name="action" value="draft" class="btn btn-secondary">
                下書き保存
            </button>
            <button type="submit" name="action" value="submit" class="btn btn-primary">
                申請提出
            </button>
            <a href="{{ url_for('application.index') }}" class="btn btn-cancel">
                キャンセル
            </a>
        </div>
    </form>
</div>
{% endblock %}

{% block extra_js %}
<script src="{{ url_for('static', filename='js/application.js') }}"></script>
{% endblock %}
```

---

### 5.6 app/templates/application/search_resource.html（リソース検索）

```html
{% extends 'base.html' %}

{% block title %}リソース検索{% endblock %}
{% block page_title %}リソース検索{% endblock %}

{% block content %}
<div class="resource-search">
    <!-- 検索フォーム -->
    <form method="GET" action="{{ url_for('application.search_resource', application_type_id=application_type_id) }}" 
          class="search-form">
        <div class="form-row">
            <div class="form-group">
                <label for="search_keyword">キーワード</label>
                <input type="text" id="search_keyword" name="search_keyword" 
                       class="form-control" value="{{ search_params.search_keyword }}">
            </div>
            
            <div class="form-group">
                <label for="owner_shozoku">所管所属</label>
                <select id="owner_shozoku" name="owner_shozoku" class="form-control">
                    <option value="">すべて</option>
                    <!-- 所属リストを動的に読み込み -->
                </select>
            </div>
            
            <div class="form-group">
                <button type="submit" class="btn btn-primary">検索</button>
            </div>
        </div>
    </form>
    
    <!-- 検索結果 -->
    <div class="search-results">
        <h3>検索結果: {{ resources|length }}件</h3>
        
        {% if resources %}
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>リソースID</th>
                    <th>表示名</th>
                    <th>所管所属</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
                {% for resource in resources %}
                <tr>
                    <td>{{ resource.resource_id }}</td>
                    <td>{{ resource.display_label }}</td>
                    <td>{{ resource.owner_shozoku }}</td>
                    <td>
                        <button type="button" 
                                class="btn btn-sm btn-primary btn-select-resource"
                                data-resource-id="{{ resource.resource_id }}"
                                data-display-label="{{ resource.display_label }}">
                            選択
                        </button>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p class="no-results">検索結果がありません。</p>
        {% endif %}
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
// リソース選択時の処理
document.querySelectorAll('.btn-select-resource').forEach(btn => {
    btn.addEventListener('click', function() {
        const resourceId = this.dataset.resourceId;
        const displayLabel = this.dataset.displayLabel;
        
        // 親ウィンドウに値を設定（モーダルの場合）
        if (window.opener) {
            window.opener.setSelectedResource(resourceId, displayLabel);
            window.close();
        }
    });
});
</script>
{% endblock %}
```

---

### 5.7 app/templates/approval/task_list.html（承認待ちタスク一覧）

```html
{% extends 'base.html' %}

{% block title %}承認待ちタスク一覧{% endblock %}
{% block page_title %}承認待ちタスク一覧{% endblock %}

{% block content %}
<div class="approval-task-list">
    <!-- フィルタ -->
    <form method="GET" action="{{ url_for('approval.task_list') }}" class="filter-form">
        <div class="form-row">
            <div class="form-group">
                <label for="application_type_id">申請種類</label>
                <select id="application_type_id" name="application_type_id" class="form-control">
                    <option value="">すべて</option>
                    <!-- 申請種類リストを動的に読み込み -->
                </select>
            </div>
            
            <div class="form-group">
                <button type="submit" class="btn btn-primary">絞り込み</button>
                <a href="{{ url_for('approval.task_list') }}" class="btn btn-secondary">クリア</a>
            </div>
        </div>
    </form>
    
    <!-- タスク一覧 -->
    <div class="task-count">
        <p>承認待ちタスク: <strong>{{ tasks|length }}</strong>件</p>
    </div>
    
    {% if tasks %}
    <table class="table table-striped table-hover">
        <thead>
            <tr>
                <th>申請ID</th>
                <th>申請種類</th>
                <th>申請区分</th>
                <th>申請タイトル</th>
                <th>申請者</th>
                <th>申請日</th>
                <th>現在のノード</th>
                <th>経過日数</th>
                <th>緊急度</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>
            {% for task in tasks %}
            <tr class="urgency-{{ 'high' if task.days_pending >= 7 else ('medium' if task.days_pending >= 3 else 'low') }}">
                <td>{{ task.application_id }}</td>
                <td>{{ task.application_type_name }}</td>
                <td>
                    {% if task.action_type == 'create' %}新規作成
                    {% elif task.action_type == 'modify' %}修正
                    {% elif task.action_type == 'delete' %}削除
                    {% endif %}
                </td>
                <td>{{ task.application_title }}</td>
                <td>{{ task.applicant_name }}</td>
                <td>{{ task.submitted_at|format_date }}</td>
                <td>{{ task.node_name }}</td>
                <td>{{ task.days_pending }}日</td>
                <td>
                    {% if task.days_pending >= 7 %}
                    <span class="badge badge-danger">遅延</span>
                    {% elif task.days_pending >= 3 %}
                    <span class="badge badge-warning">注意</span>
                    {% else %}
                    <span class="badge badge-success">正常</span>
                    {% endif %}
                </td>
                <td>
                    <a href="{{ url_for('approval.task_detail', node_instance_id=task.node_instance_id) }}" 
                       class="btn btn-sm btn-primary">
                        詳細
                    </a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <!-- ページネーション -->
    {% include 'components/pagination.html' %}
    
    {% else %}
    <div class="no-tasks">
        <p>承認待ちのタスクはありません。</p>
    </div>
    {% endif %}
</div>
{% endblock %}
```

---

### 5.8 app/templates/approval/task_detail.html（タスク詳細・承認）

```html
{% extends 'base.html' %}

{% block title %}タスク詳細 - 申請ID: {{ application.application_id }}{% endblock %}
{% block page_title %}タスク詳細{% endblock %}

{% block content %}
<div class="approval-task-detail">
    <!-- 申請基本情報 -->
    <section class="info-section">
        <h2>申請基本情報</h2>
        <table class="info-table">
            <tr>
                <th>申請ID</th>
                <td>{{ application.application_id }}</td>
            </tr>
            <tr>
                <th>申請種類</th>
                <td>{{ application.application_type_name }}</td>
            </tr>
            <tr>
                <th>申請区分</th>
                <td>
                    {% if application.action_type == 'create' %}新規作成
                    {% elif application.action_type == 'modify' %}修正
                    {% elif application.action_type == 'delete' %}削除
                    {% endif %}
                </td>
            </tr>
            <tr>
                <th>申請タイトル</th>
                <td>{{ application.application_title }}</td>
            </tr>
            <tr>
                <th>申請者</th>
                <td>{{ application.applicant_name }} ({{ application.applicant_shozoku }})</td>
            </tr>
            <tr>
                <th>申請日時</th>
                <td>{{ application.submitted_at|format_date }}</td>
            </tr>
            {% if application.target_user_id %}
            <tr>
                <th>申請対象ユーザー</th>
                <td>{{ application.target_user_name }} ({{ application.target_shozoku }})</td>
            </tr>
            {% endif %}
            {% if application.jurisdiction_shozoku %}
            <tr>
                <th>リソース所管</th>
                <td>{{ application.jurisdiction_shozoku }}</td>
            </tr>
            {% endif %}
        </table>
    </section>
    
    <!-- 申請内容 -->
    <section class="info-section">
        <h2>申請内容</h2>
        <table class="info-table">
            {% for detail in details %}
            <tr>
                <th>{{ detail.field_name }}</th>
                <td>{{ detail.field_value or detail.field_value_large }}</td>
            </tr>
            {% endfor %}
        </table>
        
        {% if application.remarks %}
        <div class="remarks">
            <h3>備考</h3>
            <p>{{ application.remarks }}</p>
        </div>
        {% endif %}
    </section>
    
    <!-- 承認履歴 -->
    <section class="info-section">
        <h2>承認履歴</h2>
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>ノード</th>
                    <th>処理</th>
                    <th>処理者</th>
                    <th>処理日時</th>
                    <th>コメント</th>
                </tr>
            </thead>
            <tbody>
                {% for h in history %}
                <tr>
                    <td>{{ h.node_name }}</td>
                    <td>
                        {% if h.action_type == 'approve' %}承認
                        {% elif h.action_type == 'reject' %}却下
                        {% elif h.action_type == 'return' %}差戻
                        {% elif h.action_type == 'skip' %}スキップ
                        {% endif %}
                    </td>
                    <td>{{ h.action_user_name }}</td>
                    <td>{{ h.actioned_at|format_date }}</td>
                    <td>{{ h.action_comment }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </section>
    
    <!-- 承認アクション -->
    <section class="action-section">
        <h2>承認アクション</h2>
        
        <form method="POST" id="approvalForm">
            <div class="form-group">
                <label for="comment">コメント</label>
                <textarea id="comment" name="comment" class="form-control" rows="5"></textarea>
            </div>
            
            <div class="form-actions">
                <button type="button" class="btn btn-success btn-lg" onclick="submitApproval('approve')">
                    承認
                </button>
                <button type="button" class="btn btn-danger btn-lg" onclick="submitApproval('reject')">
                    却下
                </button>
                <a href="{{ url_for('approval.task_list') }}" class="btn btn-secondary">
                    戻る
                </a>
            </div>
        </form>
    </section>
</div>
{% endblock %}

{% block extra_js %}
<script>
function submitApproval(action) {
    const form = document.getElementById('approvalForm');
    const comment = document.getElementById('comment').value;
    
    if (action === 'reject' && !comment.trim()) {
        alert('却下する場合はコメントを入力してください。');
        return;
    }
    
    if (action === 'approve') {
        if (!confirm('承認してよろしいですか?')) {
            return;
        }
        form.action = "{{ url_for('approval.approve', node_instance_id=node_instance.node_instance_id) }}";
    } else if (action === 'reject') {
        if (!confirm('却下してよろしいですか?\nこの操作は取り消せません。')) {
            return;
        }
        form.action = "{{ url_for('approval.reject', node_instance_id=node_instance.node_instance_id) }}";
    }
    
    form.submit();
}
</script>
{% endblock %}
```

---

## 6. 主要なJavaScriptファイル

### 6.1 app/static/js/application.js

```javascript
/**
 * 申請画面用JavaScript
 */

// リソース検索モーダルを開く
document.querySelectorAll('.btn-search-resource').forEach(btn => {
    btn.addEventListener('click', function() {
        const fieldId = this.dataset.fieldId;
        const applicationTypeId = document.getElementById('applicationForm').dataset.applicationTypeId;
        
        // モーダルウィンドウを開く
        const url = `/application/search_resource/${applicationTypeId}?field_id=${fieldId}`;
        window.open(url, 'ResourceSearch', 'width=800,height=600,scrollbars=yes');
    });
});

// リソース選択結果を受け取る
function setSelectedResource(resourceId, displayLabel) {
    const fieldId = window.currentFieldId;
    document.getElementById(`field_${fieldId}`).value = resourceId;
    document.getElementById(`field_${fieldId}_display`).value = displayLabel;
}

// フォームのバリデーション
document.getElementById('applicationForm')?.addEventListener('submit', function(e) {
    const requiredFields = this.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('error');
        } else {
            field.classList.remove('error');
        }
    });
    
    if (!isValid) {
        e.preventDefault();
        alert('必須項目を入力してください。');
    }
});

// プルダウン選択肢の動的読み込み
function loadPulldownOptions(fieldId, pulldownGroupId) {
    fetch(`/api/pulldown_options/${pulldownGroupId}`)
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById(`field_${fieldId}`);
            data.options.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.value = option.option_value;
                optionElement.textContent = option.option_label;
                select.appendChild(optionElement);
            });
        })
        .catch(error => {
            console.error('プルダウン選択肢の読み込みエラー:', error);
        });
}
```

---

## 7. まとめ

この構成により、以下が実現されます:

### アプリケーション構造の特徴

1. **3層アーキテクチャ**
   - Models: データアクセス層
   - Services: ビジネスロジック層
   - Routes: コントローラー層

2. **テンプレート継承**
   - base.htmlを基底とした一貫したUI
   - 再利用可能なコンポーネント

3. **分離された関心事**
   - 各ファイルが単一の責務を持つ
   - メンテナンス性・テスト容易性の向上

4. **拡張性**
   - 新しい申請種類の追加が容易
   - ワークフロー定義の柔軟な変更

5. **セキュリティ**
   - デコレーターによる認証チェック
   - 権限チェックの実装

これらのファイル構成により、要件を満たすFlaskアプリケーションを構築できます。
