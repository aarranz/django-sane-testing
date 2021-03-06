# -*- coding: utf-8 -*-
from djangosanetesting.cases import UnitTestCase
from djangosanetesting.utils import mock_settings

from django.core.cache import cache
from django.conf import settings

from testapp.models import ExampleModel

class TestUnitSimpleMetods(UnitTestCase):
    def test_true(self):
        self.assert_true(True)
    
    def test_true_false(self):
        self.assert_raises(AssertionError, lambda:self.assert_true(False))
    
    def raise_value_error(self):
        # lambda cannot do it, fix Python
        raise ValueError()
    
    def test_raises(self):
        self.assert_true(True, self.assert_raises(ValueError, lambda:self.raise_value_error()))
    
    def test_raises_raise_assertion(self):
        self.assert_raises(AssertionError, lambda: self.assert_raises(ValueError, lambda: "a"))
    
    def test_equals(self):
        self.assert_equals(1, 1)

    def test_equals_false(self):
        self.assert_raises(AssertionError, lambda:self.assert_equals(1, 2))

    def test_fail(self):
        try:
            self.fail()
        except AssertionError:
            pass
        else:
            raise AssertionError("self.fail should raise AssertionError")
    
    def test_new_unittest_methods_imported(self):
        try:
            import unittest2
        except ImportError:
            import sys
            if sys.version_info[0] == 2 and sys.version_info[1] < 7:
                raise self.SkipTest("Special assert functions not available")

        self.assert_in(1, [1])

    
class TestUnitAliases(UnitTestCase):
    
    def get_camel(self, name):
        """ Transform under_score_names to underScoreNames """
        if name.startswith("_") or name.endswith("_"):
            raise ValueError(u"Cannot ransform to CamelCase world when name begins or ends with _")
        
        camel = list(name)
        
        while "_" in camel:
            index = camel.index("_")
            del camel[index]
            if camel[index] is "_":
                raise ValueError(u"Double underscores are not allowed")
            camel[index] = camel[index].upper()
        return ''.join(camel)
    
    def test_camelcase_aliases(self):
        for i in ["assert_true", "assert_equals", "assert_false", "assert_almost_equals"]:
            #FIXME: yield tests after #12 is resolved
            #yield lambda x, y: self.assert_equals, getattr(self, i), getattr(self, self.get_camel(i))
            self.assert_equals(getattr(self, i), getattr(self, self.get_camel(i)))
    
    def test_get_camel(self):
        self.assert_equals("assertTrue", self.get_camel("assert_true"))
    
    def test_get_camel_invalid_trail(self):
        self.assert_raises(ValueError, lambda:self.get_camel("some_trailing_test_"))

    def test_get_camel_invalid_double_under(self):
        self.assert_raises(ValueError, lambda:self.get_camel("toomuchtrail__between"))
                           
    def test_get_camel_invalid_prefix(self):
        self.assert_raises(ValueError, lambda:self.get_camel("_prefix"))


class TestFeatures(UnitTestCase):

    def test_even_unit_can_access_views(self):
        self.assert_equals(200, self.client.get("/testtwohundred/").status_code)

class TestProperClashing(UnitTestCase):
    """
    Test we're getting expected failures when working with db,
    i.e. that database is not purged between tests.
    We rely that test suite executed methods in this order:
      (1) test_aaa_inserting_model
      (2) test_bbb_inserting_another
      
    This is antipattern and should not be used, but it's hard to test
    framework from within ;) Better solution would be greatly appreciated.  
    """
    
    def test_aaa_inserting_model(self):
        ExampleModel.objects.create(name="test1")
        self.assert_equals(1, len(ExampleModel.objects.all()))

    def test_bbb_inserting_another(self):
        ExampleModel.objects.create(name="test2")
        self.assert_equals(2, len(ExampleModel.objects.all()))


class TestProperCacheClearance(UnitTestCase):
    """
    Test cache is cleared, i.e. not preserved between tests
    We rely that test suite executed methods in this order:
      (1) test_aaa_inserting_cache
      (2) test_bbb_cache_retrieval

    This is antipattern and should not be used, but it's hard to test
    framework from within ;) Better solution would be greatly appreciated.
    """

    def test_aaa_inserting_model(self):
        cache.set("test", "pwned")
        self.assert_equals("pwned", cache.get("test"))

    def test_bbb_inserting_another(self):
        self.assert_equals(None, cache.get("test"))


class TestTranslations(UnitTestCase):
    def test_czech_string_acquired(self):
        """
        Test we're retrieving string translated to Czech.
        This is assuming we're using LANG="cs"
        """
        self.assert_equals(u"Přeložitelný řetězec", unicode(ExampleModel.get_translated_string()))


#TODO: This is not working, looks like once you cannot return to null translations
# once you have selected any. Patches welcomed.
#class TestSkippedTranslations(UnitTestCase):
#    make_translations=False
#
#    def test_english_string_acquired(self):
#        from django.utils import translation
#        translation.deactivate()
#        self.assert_equals(u"Translatable string", unicode(ExampleModel.get_translated_string()))

class TestNotDefaultTranslations(UnitTestCase):
    translation_language_code = 'de'
    def test_german_translated_string_acquired(self):
        self.assert_equals(u"Ersetzbare Zeichenkette", unicode(ExampleModel.get_translated_string()))


def function_test():
    # just to verify we work with them
    assert True is True

class TestMocking(UnitTestCase):

    def test_sanity_for_missing_setting_present(self):
        self.assert_false(hasattr(settings, "INSANE_ATTRIBUTE_THAT_SHOULD_NOT_BE_PRESENT"))
    
    def test_expected_setting_present(self):
        self.assert_equals("owned", settings.NONSENSICAL_SETTING_ATTRIBUTE_FOR_MOCK_TESTING)

    @mock_settings("INSANE_ATTRIBUTE_THAT_SHOULD_NOT_BE_PRESENT", "Cthulhed!")
    def test_setting_mocked(self):
        self.assert_equals("Cthulhed!", settings.INSANE_ATTRIBUTE_THAT_SHOULD_NOT_BE_PRESENT)

    @mock_settings("NONSENSICAL_SETTING_ATTRIBUTE_FOR_MOCK_TESTING", "pwned!")
    def test_existing_setting_mocked(self):
        self.assert_equals("pwned!", settings.NONSENSICAL_SETTING_ATTRIBUTE_FOR_MOCK_TESTING)

class TestMockingCleansAfterItself(UnitTestCase):
    @mock_settings("INSANE_ATTRIBUTE_THAT_SHOULD_NOT_BE_PRESENT", "Cthulhed!")
    def test_aaa_mocked(self):
        self.assert_equals("Cthulhed!", settings.INSANE_ATTRIBUTE_THAT_SHOULD_NOT_BE_PRESENT)

    def test_bbb_attribute_not_present(self):
        self.assert_false(hasattr(settings, "INSANE_ATTRIBUTE_THAT_SHOULD_NOT_BE_PRESENT"))
    