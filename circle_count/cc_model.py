import os
import shutil

import keras

from common import data_dir
from common import vis_utils as vis
import circle_count as cc
import img_utils as img

MODEL_NAME_PREFIX = "circle_count"
MODEL_BASE_DIR = os.path.join(data_dir, "model")

TRAIN_EPOCHS = 10


class Model:
    def __init__(self, params):
        self.__compiled = False
        self._params = params
        self.model = None

    def build(self):
        if self.model is not None:
            raise Exception("model is initialized")

        self._construct_model()
        self._construct_input_layer()
        self._construct_fc_layer()
        self._construct_output_layer()
        self.model.summary()

    def load(self, compile=False):
        if self.model is not None:
            raise Exception("model is initialized")

        model_path, _ = self.__get_model_path()
        self.model = keras.models.load_model(model_path, compile=compile)
        print(model_path, "loaded")
        self.model.summary()
        self.__compiled = compile

    def save(self, ask=False):
        if ask:
            save = input('save model ["{}"]? (y|n): '.format(self.model.name))
            if save != "y":
                print("model [{}] not saved".format(self.model.name))
                return

        model_path, model_old_path = self.__get_model_path()
        if os.path.exists(model_path):
            if os.path.exists(model_old_path):
                shutil.rmtree(model_old_path)
            os.rename(model_path, model_old_path)
        self.model.save(model_path)
        print("model [" + self.model.name + "] saved")

    def show(self):
        if self.model is None:
            raise Exception("model is not initialized, call build or load method")
        vis.build_model_figure(self.model)
        vis.show_all()

    def compile(self, learning_rate=cc.LEARNING_RATE):
        if self.model is None:
            raise Exception("model is not initialized, call build or load method")

        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate),
            loss=self._get_loss(),
            metrics=self._get_metrics(),
        )
        self.__compiled = True

    def train(self, data, epochs=TRAIN_EPOCHS, test_data=None):
        if not self.__compiled:
            raise Exception("model is not compiled yet, call compile first")

        train_data, test_data = cc.dataset.prepare_data(data)

        self.model.fit(
            train_data,
            epochs=epochs,
            validation_data=test_data,
            callbacks=[
                vis.matplotlib_callback(show_model=False, show_metrics=False),
                vis.tensorboard_callback("circle_count"),
            ],
        )

    def predict(self, x):
        if self.model is None:
            raise Exception("model is not initialized, call build or load method first")

        x, _ = self._pre_process(x, None)
        prediction = self.model.predict(x)

        return prediction

    def evaluate(self, data):
        if self.model is None:
            raise Exception("model is not initialized, call build or load method first")

        x, y = data
        x, y = self._pre_process(x, y)

        return self.model.evaluate(x, y)

    def verify(self, data):
        if self.model is None:
            raise Exception("model is not initialized, call build or load method first")

        if not self.__compiled:
            raise Exception("model is not compiled yet, call compile first")

        x, y = data
        x, y = self._pre_process(x, y)

        evaluation = self.model.evaluate(x, y)
        print("evaluation: ", evaluation)

        preds = self.model.predict(x)
        img.show_images(data, preds, title="predict result")

    def _construct_model(self):
        self.model = keras.Sequential(name=self._get_model_name())

    def _construct_input_layer(self):
        input_shape = self._params["input_shape"]
        self.model.add(keras.layers.Flatten(input_shape=input_shape))

    def _construct_fc_layer(self):
        layers = self._params["fc_layers"]
        units = self._params["fc_layers_units"]
        for _ in range(layers):
            self.model.add(keras.layers.Dense(units, activation="relu"))

    def _construct_output_layer(self):
        raise NotImplementedError(
            f"Model {self.__class__.__name__} does not have a `_construct_output_layer()` "
            "method implemented."
        )

    def _get_model_name(self):
        layers = self._params["fc_layers"]
        units = self._params["fc_layers_units"]
        return "{}.{}.fc{}-{}".format(
            MODEL_NAME_PREFIX, self.__class__.__name__, layers, units
        )

    def _get_loss(self):
        raise NotImplementedError(
            f"Model {self.__class__.__name__} does not have a `_construct_output_layer()` "
            "method implemented."
        )

    def _get_metrics(self):
        return ["accuracy"]

    def _pre_process(self, x, y):
        return cc.dataset.pre_process(x, y)

    def _post_process(self, data):
        return data

    def __get_model_path(self):
        if self.model:
            name = self.model.name
        else:
            name = self._get_model_name()
        return os.path.join(MODEL_BASE_DIR, name), os.path.join(
            MODEL_BASE_DIR, name + ".old"
        )


class ClassificationModel(Model):
    def __init__(self, params):
        super().__init__(params)

    def _get_loss(self):
        return "sparse_categorical_crossentropy"

    def _construct_output_layer(self):
        output_units = self._params["output_units"]
        self.model.add(keras.layers.Dense(output_units, activation="softmax"))


class RegressionModel(Model):
    def __init__(self, params):
        super().__init__(params)

    def _get_loss(self):
        return "mean_squared_error"

    def _construct_output_layer(self):
        self.model.add(keras.layers.Dense(1))


class ConvModel(Model):
    def _get_model_name(self):
        layers = self._params["conv_layers"]
        filters = self._params["conv_filters"]
        return "{}.conv{}-{}".format(super()._get_model_name(), layers, filters)

    def _construct_input_layer(self):
        input_shape = self._params["input_shape"]
        self.model.add(
            keras.layers.Conv2D(32, (3, 3), activation="relu", input_shape=input_shape)
        )
        layers = self._params["conv_layers"]
        filters = self._params["conv_filters"]
        for _ in range(layers):
            self.model.add(keras.layers.Conv2D(filters, (3, 3), activation="relu"))
            self.model.add(keras.layers.MaxPooling2D())
        self.model.add(keras.layers.Flatten())


class ConvRegModel(RegressionModel, ConvModel):
    pass


class ConvClsModel(ClassificationModel, ConvModel):
    pass


def new_model(params=cc.REG_MODEL_PARAMS):
    type = params["model_type"]
    if not type:
        type = RegressionModel
    if isinstance(type, str):
        model_class = globals()[type]
    else:
        model_class = type
    if model_class and issubclass(model_class, Model):
        return model_class(params)
    else:
        raise Exception("no such model %s" % type)


def load_model(params=cc.REG_MODEL_PARAMS, compile=False):
    type = params["model_type"]
    if isinstance(type, str):
        model_class = globals()[type]
    else:
        model_class = type
    if model_class and issubclass(model_class, Model):
        model = model_class(params)
        model.load(compile=compile)
        return model
    else:
        raise Exception("no such model %s" % type)


if __name__ == "__main__":
    import circle_count.data_utils as dutils

    # data = dutils.gen_sample_data(size=20)
    data = dutils.gen_sample_data(get_config=cc.data_config((6, 6), (6, 7)), size=20)
    # data = dutils.load_data()
    # data = dutils.load_error_data()
    # data = dutils.load_error_data(error_gt=0.2)

    # params = cc.REG_MODEL_PARAMS
    # params = cc.CLS_MODEL_PARAMS
    params = cc.CONV_REG_MODEL_PARAMS
    # params = cc.CONV_CLS_MODEL_PARAMS
    model = load_model(params, compile=True)
    model.show()
    model.verify(data)
