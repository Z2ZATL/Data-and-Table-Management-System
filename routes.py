from flask import render_template, redirect, url_for, flash, request, abort
from app import app, db
from forms import ContactForm
from models import FormSubmission

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/form', methods=['GET', 'POST'])
def contact_form():
    form = ContactForm()
    
    if form.validate_on_submit():
        # Create a new form submission record
        submission = FormSubmission(
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            message=form.message.data
        )
        
        # Save to the database
        db.session.add(submission)
        db.session.commit()
        
        # Flash success message and redirect
        flash('Your form has been submitted successfully!', 'success')
        return redirect(url_for('success'))
    
    # If there are validation errors, they'll be displayed in the template
    return render_template('form.html', form=form)

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/admin')
def admin():
    # Get all submissions from the database
    submissions = FormSubmission.query.order_by(FormSubmission.submission_date.desc()).all()
    return render_template('admin.html', submissions=submissions)

@app.route('/admin/submission/<int:submission_id>')
def view_submission(submission_id):
    # Get the specific submission or return 404
    submission = FormSubmission.query.get_or_404(submission_id)
    return render_template('view_submission.html', submission=submission)
