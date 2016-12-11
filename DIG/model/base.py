"""Base classes for all models."""

import copy
import warnings

import numpy as np
from scipy import sparse
from DIG.externals import six
from DIG.util.fixes import signature
from DIG.IO.pretty_print import pprint


class BaseModel(object):
    """Base class for all Models in DIG

    Notes
    -----
    All Models should specify all the parameters that can be set
    at the class level in their ``__init__`` as explicit keyword
    arguments (no ``*args`` or ``**kwargs``).
    """

    @classmethod
    def _get_param_names(cls):
        """Get parameter names for the Model"""
        # fetch the constructor or the original constructor before
        # deprecation wrapping if any
        init = getattr(cls.__init__, 'deprecated_original', cls.__init__)
        if init is object.__init__:
            # No explicit constructor to introspect
            return []

        # introspect the constructor arguments to find the model parameters
        # to represent
        init_signature = signature(init)
        # Consider the constructor parameters excluding 'self'
        parameters = [p for p in init_signature.parameters.values()
                      if p.name != 'self' and p.kind != p.VAR_KEYWORD]
        for p in parameters:
            if p.kind == p.VAR_POSITIONAL:
                raise RuntimeError("DIG Models should always "
                                   "specify their parameters in the signature"
                                   " of their __init__ (no varargs)."
                                   " %s with constructor %s doesn't "
                                   " follow this convention."
                                   % (cls, init_signature))
        # Extract and sort argument names excluding 'self'
        return sorted([p.name for p in parameters])

    def get_params(self, deep=True):
        """Get parameters for this Model.

        Parameters
        ----------
        deep: boolean, optional
            If True, will return the parameters for this Model and
            contained subobjects that are Models.

        Returns
        -------
        params : mapping of string to any
            Parameter names mapped to their values.
        """
        out = dict()
        for key in self._get_param_names():
            # We need deprecation warnings to always be on in order to
            # catch deprecated param values.
            # This is set in utils/__init__.py but it gets overwritten
            # when running under python3 somehow.
            warnings.simplefilter("always", DeprecationWarning)
            try:
                with warnings.catch_warnings(record=True) as w:
                    value = getattr(self, key, None)
                if len(w) and w[0].category == DeprecationWarning:
                    # if the parameter is deprecated, don't show it
                    continue
            finally:
                warnings.filters.pop(0)

            # XXX: should we rather test if instance of Model?
            if deep and hasattr(value, 'get_params'):
                deep_items = value.get_params().items()
                out.update((key + '__' + k, val) for k, val in deep_items)
            out[key] = value
        return out

    def set_params(self, **params):
        """Set the parameters of this Model.

        The method works on simple Models as well as on nested objects
        (such as pipelines). The latter have parameters of the form
        ``<component>__<parameter>`` so that it's possible to update each
        component of a nested object.

        Returns
        -------
        self
        """
        if not params:
            # Simple optimisation to gain speed (inspect is slow)
            return self
        valid_params = self.get_params(deep=True)
        for key, value in six.iteritems(params):
            split = key.split('__', 1)
            if len(split) > 1:
                # nested objects case
                name, sub_name = split
                if name not in valid_params:
                    raise ValueError('Invalid parameter %s for Model %s. '
                                     'Check the list of available parameters '
                                     'with `Model.get_params().keys()`.' %
                                     (name, self))
                sub_object = valid_params[name]
                sub_object.set_params(**{sub_name: value})
            else:
                # simple objects case
                if key not in valid_params:
                    raise ValueError('Invalid parameter %s for Model %s. '
                                     'Check the list of available parameters '
                                     'with `Model.get_params().keys()`.' %
                                     (key, self.__class__.__name__))
                setattr(self, key, value)
        return self

    def __repr__(self):
        class_name = self.__class__.__name__
        return '%s(%s)' % (class_name, pprint(self.get_params(deep=False),
                                               offset=len(class_name),),)


class ClassifierMixin(object):
    """Mixin class for all classifiers in DIG."""
    _Model_type = "classifier"

    def score(self, X, y, sample_weight=None):
        """Returns the mean accuracy on the given test data and labels.

        In multi-label classification, this is the subset accuracy
        which is a harsh metric since you require for each sample that
        each label set be correctly predicted.

        Parameters
        ----------
        X : array-like, shape = (n_samples, n_features)
            Test samples.

        y : array-like, shape = (n_samples) or (n_samples, n_outputs)
            True labels for X.

        sample_weight : array-like, shape = [n_samples], optional
            Sample weights.

        Returns
        -------
        score : float
            Mean accuracy of self.predict(X) wrt. y.

        """
        from .metrics import accuracy_score
        return accuracy_score(y, self.predict(X), sample_weight=sample_weight)


class RegressorMixin(object):
    """Mixin class for all regression Models in DIG."""
    _Model_type = "regressor"

    def score(self, X, y, sample_weight=None):
        """Returns the coefficient of determination R^2 of the prediction.

        The coefficient R^2 is defined as (1 - u/v), where u is the regression
        sum of squares ((y_true - y_pred) ** 2).sum() and v is the residual
        sum of squares ((y_true - y_true.mean()) ** 2).sum().
        Best possible score is 1.0 and it can be negative (because the
        model can be arbitrarily worse). A constant model that always
        predicts the expected value of y, disregarding the input features,
        would get a R^2 score of 0.0.

        Parameters
        ----------
        X : array-like, shape = (n_samples, n_features)
            Test samples.

        y : array-like, shape = (n_samples) or (n_samples, n_outputs)
            True values for X.

        sample_weight : array-like, shape = [n_samples], optional
            Sample weights.

        Returns
        -------
        score : float
            R^2 of self.predict(X) wrt. y.
        """

        from .metrics import r2_score
        return r2_score(y, self.predict(X), sample_weight=sample_weight,
                        multioutput='variance_weighted')


class ClusterMixin(object):
    """Mixin class for all cluster Models in DIG."""
    _Model_type = "clusterer"

    def fit_predict(self, X, y=None):
        """Performs clustering on X and returns cluster labels.

        Parameters
        ----------
        X : ndarray, shape (n_samples, n_features)
            Input data.

        Returns
        -------
        y : ndarray, shape (n_samples,)
            cluster labels
        """
        # non-optimized default implementation; override when a better
        # method is possible for a given clustering algorithm
        self.fit(X)
        return self.labels_

class TransformerMixin(object):
    """Mixin class for all transformers in DIG."""

    def fit_transform(self, X, y=None, **fit_params):
        """Fit to data, then transform it.

        Fits transformer to X and y with optional parameters fit_params
        and returns a transformed version of X.

        Parameters
        ----------
        X : numpy array of shape [n_samples, n_features]
            Training set.

        y : numpy array of shape [n_samples]
            Target values.

        Returns
        -------
        X_new : numpy array of shape [n_samples, n_features_new]
            Transformed array.

        """
        # non-optimized default implementation; override when a better
        # method is possible for a given clustering algorithm
        if y is None:
            # fit method of arity 1 (unsupervised transformation)
            return self.fit(X, **fit_params).transform(X)
        else:
            # fit method of arity 2 (supervised transformation)
            return self.fit(X, y, **fit_params).transform(X)


class DensityMixin(object):
    """Mixin class for all density Models in DIG."""
    _Model_type = "DensityModel"

    def score(self, X, y=None):
        """Returns the score of the model on the data X

        Parameters
        ----------
        X : array-like, shape = (n_samples, n_features)

        Returns
        -------
        score: float
        """
        pass

def _first_and_last_element(arr):
    """Returns first and last element of numpy array or sparse matrix."""
    if isinstance(arr, np.ndarray) or hasattr(arr, 'data'):
        # numpy array or sparse matrix with .data attribute
        data = arr.data if sparse.issparse(arr) else arr
        return data.flat[0], data.flat[-1]
    else:
        # Sparse matrices without .data attribute. Only dok_matrix at
        # the time of writing, in this case indexing is fast
        return arr[0, 0], arr[-1, -1]


def clone(Model, safe=True):
    """Constructs a new Model with the same parameters.

    Clone does a deep copy of the model in a Model
    without actually copying attached data. It yields a new Model
    with the same parameters that has not been fit on any data.

    Parameters
    ----------
    Model: Model object, or list, tuple or set of objects
        The Model or group of Models to be cloned

    safe: boolean, optional
        If safe is false, clone will fall back to a deepcopy on objects
        that are not Models.

    """
    Model_type = type(Model)
    # XXX: not handling dictionaries
    if Model_type in (list, tuple, set, frozenset):
        return Model_type([clone(e, safe=safe) for e in Model])
    elif not hasattr(Model, 'get_params'):
        if not safe:
            return copy.deepcopy(Model)
        else:
            raise TypeError("Cannot clone object '%s' (type %s): "
                            "it does not seem to be a DIG Model "
                            "as it does not implement a 'get_params' methods."
                            % (repr(Model), type(Model)))
    klass = Model.__class__
    new_object_params = Model.get_params(deep=False)
    for name, param in six.iteritems(new_object_params):
        new_object_params[name] = clone(param, safe=False)
    new_object = klass(**new_object_params)
    params_set = new_object.get_params(deep=False)

    # quick sanity check of the parameters of the clone
    for name in new_object_params:
        param1 = new_object_params[name]
        param2 = params_set[name]
        if isinstance(param1, np.ndarray):
            # For most ndarrays, we do not test for complete equality
            if not isinstance(param2, type(param1)):
                equality_test = False
            elif (param1.ndim > 0
                    and param1.shape[0] > 0
                    and isinstance(param2, np.ndarray)
                    and param2.ndim > 0
                    and param2.shape[0] > 0):
                equality_test = (
                    param1.shape == param2.shape
                    and param1.dtype == param2.dtype
                    and (_first_and_last_element(param1) ==
                         _first_and_last_element(param2))
                )
            else:
                equality_test = np.all(param1 == param2)
        elif sparse.issparse(param1):
            # For sparse matrices equality doesn't work
            if not sparse.issparse(param2):
                equality_test = False
            elif param1.size == 0 or param2.size == 0:
                equality_test = (
                    param1.__class__ == param2.__class__
                    and param1.size == 0
                    and param2.size == 0
                )
            else:
                equality_test = (
                    param1.__class__ == param2.__class__
                    and (_first_and_last_element(param1) ==
                         _first_and_last_element(param2))
                    and param1.nnz == param2.nnz
                    and param1.shape == param2.shape
                )
        else:
            new_obj_val = new_object_params[name]
            params_set_val = params_set[name]
            # The following construct is required to check equality on special
            # singletons such as np.nan that are not equal to them-selves:
            equality_test = (new_obj_val == params_set_val or
                             new_obj_val is params_set_val)
        if not equality_test:
            raise RuntimeError('Cannot clone object %s, as the constructor '
                               'does not seem to set parameter %s' %
                               (Model, name))

    return new_object


def is_classifier(Model):
    """Returns True if the given Model is (probably) a classifier."""
    return getattr(Model, "_Model_type", None) == "classifier"


def is_regressor(Model):
    """Returns True if the given Model is (probably) a regressor."""
    return getattr(Model, "_Model_type", None) == "regressor"

