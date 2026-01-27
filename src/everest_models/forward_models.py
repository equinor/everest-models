from importlib import resources
from importlib.util import find_spec
from typing import Final, List, Type

_HAVE_ERT: Final = find_spec("ert") is not None


def get_forward_models() -> List[str]:
    """Return the list of forward model names."""
    return [
        job.name[3:]
        for job in resources.files("everest_models.jobs").iterdir()
        if job.name.startswith("fm_")
    ]


if _HAVE_ERT:  # The everest-models package should remain installable without ERT.
    import ert
    from ert import ForwardModelStepDocumentation, ForwardModelStepPlugin

    def build_forward_model_step_plugin(fm_name: str) -> Type[ForwardModelStepPlugin]:
        class_name = "".join(x.capitalize() for x in fm_name.lower().split("_"))
        return type(
            class_name,
            (ForwardModelStepPlugin,),
            {
                "__init__": lambda x: ForwardModelStepPlugin.__init__(
                    x, name=fm_name, command=[f"fm_{fm_name}"]
                ),
                "__module__": __name__,
                "documentation": lambda: ForwardModelStepDocumentation(
                    category="everest.everest_models",
                    source_package="everest_models",
                    source_function_name=class_name,
                    description=f"The {fm_name} forward model.",
                ),
            },
        )

    @ert.plugin(name="everest_models")
    def installable_forward_model_steps():
        return [
            build_forward_model_step_plugin(fm_name) for fm_name in get_forward_models()
        ]
