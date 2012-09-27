import functools
import os

from django.core.exceptions import ImproperlyConfigured
from django.core import mail
from django.test import TestCase
from django.template import Context, Template, TemplateDoesNotExist

from mailview.messages import (TemplatedEmailMessageView,
    TemplatedHTMLEmailMessageView)


try:
    from django.test.utils import override_settings
except ImportError:
    from mailview.tests.utils import override_settings


using_test_templates = override_settings(
    TEMPLATE_DIRS=(
        os.path.join(os.path.dirname(__file__), 'templates'),
    ),
    TEMPLATE_LOADERS=(
        'django.template.loaders.filesystem.Loader',
    )
)


class EmailMessageViewTestCaseMixin(object):
    def run(self, *args, **kwargs):
        with using_test_templates:
            return super(EmailMessageViewTestCaseMixin, self).run(*args, **kwargs)


class TemplatedEmailMessageViewTestCase(EmailMessageViewTestCaseMixin, TestCase):
    message_class = TemplatedEmailMessageView

    def setUp(self):
        self.value = 'Hello, world!'
        self.context = Context({'value': self.value})
        self.message = self.message_class()

        self.render_subject = functools.partial(self.message.render_subject,
            context=self.context)
        self.render_body = functools.partial(self.message.render_body,
            context=self.context)

    def test_subject_template_inconfigured(self):
        self.assertRaises(ImproperlyConfigured, self.render_subject)

    def test_subject_invalid_template_name(self):
        self.message.subject_template_name = 'invalid.txt'
        self.assertRaises(TemplateDoesNotExist, self.render_subject)

    def test_subject_template_name(self):
        self.message.subject_template_name = 'subject.txt'
        self.assertEqual(self.render_subject(), self.value)

    def test_subject_template(self):
        self.message.subject_template = Template('{{ value }}')
        self.assertEqual(self.render_subject(), self.value)

    def test_body_template_inconfigured(self):
        self.assertRaises(ImproperlyConfigured, self.render_body)

    def test_body_invalid_template_name(self):
        self.message.body_template_name = 'invalid.txt'
        self.assertRaises(TemplateDoesNotExist, self.render_body)

    def test_body_template_name(self):
        self.message.body_template_name = 'body.txt'
        self.assertEqual(self.render_body(), self.value + '\n')

    def test_body_template(self):
        self.message.body_template = Template('{{ value }}')
        self.assertEqual(self.render_body(), self.value)

    def test_render_to_message(self):
        template = Template('{{ value }}')
        self.message.subject_template = template
        self.message.body_template = template

        message = self.message.render_to_message(self.context)
        self.assertEqual(message.subject, self.value)
        self.assertEqual(message.body, self.value)

    def test_send(self):
        template = Template('{{ value }}')
        self.message.subject_template = template
        self.message.body_template = template

        extra_context = {'value': self.value}
        self.message.send(extra_context, to=('ted@disqus.com',))

        self.assertEqual(len(mail.outbox), 1)


class TemplatedHTMLEmailMessageViewTestCase(TemplatedEmailMessageViewTestCase):
    message_class = TemplatedHTMLEmailMessageView

    def setUp(self):
        super(TemplatedHTMLEmailMessageViewTestCase, self).setUp()
        self.render_html_body = functools.partial(self.message.render_html_body,
            context=self.context)

    def test_html_body_template_inconfigured(self):
        self.assertRaises(ImproperlyConfigured, self.render_html_body)

    def test_html_body_invalid_template_name(self):
        self.message.html_body_template_name = 'invalid.txt'
        self.assertRaises(TemplateDoesNotExist, self.render_html_body)

    def test_html_body_template_name(self):
        self.message.html_body_template_name = 'body.html'
        self.assertEqual(self.render_html_body(), self.value + '\n')

    def test_html_body_template(self):
        self.message.html_body_template = Template('{{ value }}')
        self.assertEqual(self.render_html_body(), self.value)

    def test_render_to_message(self):
        template = Template('{{ value }}')
        self.message.subject_template = template
        self.message.body_template = template
        self.message.html_body_template = template

        message = self.message.render_to_message(self.context)
        self.assertEqual(message.subject, self.value)
        self.assertEqual(message.body, self.value)
        self.assertEqual(message.alternatives, [(self.value, 'text/html')])

    def test_send(self):
        template = Template('{{ value }}')
        self.message.subject_template = template
        self.message.body_template = template
        self.message.html_body_template = template

        extra_context = {'value': self.value}
        self.message.send(extra_context, to=('ted@disqus.com',))

        self.assertEqual(len(mail.outbox), 1)
