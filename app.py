from flask import Flask, request, render_template
from clips import Environment, Symbol
import io, sys, os

app = Flask(__name__, template_folder="templates")

# Загрузка базы знаний
KB_FILE = os.path.join(os.path.dirname(__file__), "knowledge.clp")
env = Environment()
env.load(KB_FILE)


def get_form_val(form, name, default):
    """Получение значения из формы с обработкой по умолчанию"""
    v = form.get(name, "").strip()
    return v if v != "" else default


def get_fact_slot(fact, slot_name, default=""):
    """Безопасное получение значения слота из факта CLIPS для python-clips"""
    try:
        value = fact[slot_name]

        # В python-clips multislot возвращается как tuple
        if isinstance(value, tuple):
            # Преобразуем кортеж в список строк
            return [str(item) for item in value]

        # Для Symbol объектов
        elif isinstance(value, Symbol):
            return str(value)

        # Для обычных значений
        elif value is not None:
            return str(value)

        return default
    except:
        return default


@app.route("/", methods=["GET", "POST"])
def index():
    recommendations = []
    trace = ""
    calculations = []
    errors = []

    if request.method == "POST":
        # Перехватываем вывод для трассировки
        old_stdout = sys.stdout
        sys.stdout = mystdout = io.StringIO()

        try:
            env.reset()

            # Определяем тип кухни
            kitchen_type = "электрическая"
            if get_form_val(request.form, "тип_помещения", "") == "кухня":
                kitchen_type = get_form_val(request.form, "тип_кухни", "электрическая")

            # Факт помещения
            room_fact = f"""
                (помещение
                    (тип {get_form_val(request.form, "тип_помещения", "жилая_площадь")})
                    (площадь {get_form_val(request.form, "площадь", "20")})
                    (высота_потолков {get_form_val(request.form, "высота_потолков", "2.7")})
                    (кратность_воздуха 1)
                    (тип_кухни {kitchen_type})
                )
            """
            env.assert_string(room_fact)

            # Факты оборудования (если заполнены)
            supply_name = get_form_val(request.form, "приточный_элемент", "")
            if supply_name:
                supply_fact = f"""
                    (элемент_вентиляции
                        (тип приточный)
                        (название "{supply_name}")
                        (производительность {get_form_val(request.form, "производительность_приток", "0")})
                        (диаметр {get_form_val(request.form, "диаметр_приток", "0")})
                        (материал пластик)
                    )
                """
                env.assert_string(supply_fact)

            exhaust_name = get_form_val(request.form, "вытяжной_элемент", "")
            if exhaust_name:
                exhaust_fact = f"""
                    (элемент_вентиляции
                        (тип вытяжной)
                        (название "{exhaust_name}")
                        (производительность {get_form_val(request.form, "производительность_вытяжка", "0")})
                        (диаметр {get_form_val(request.form, "диаметр_вытяжка", "0")})
                        (материал металл)
                    )
                """
                env.assert_string(exhaust_fact)

            # Запуск экспертной системы
            env.run()

            # Сбор результатов
            calculation_data = {}
            for fact in env.facts():
                try:
                    # В python-clips fact.template может быть объектом, приводим к строке
                    template_name = str(fact.template)

                    if "расчет" in template_name:
                        # Получаем данные расчета через get_fact_slot
                        calculation_data["объем_воздуха"] = get_fact_slot(fact, "объем_воздуха")
                        calculation_data["рекомендуемая_производительность_притока"] = get_fact_slot(
                            fact, "рекомендуемая_производительность_притока"
                        )
                        calculation_data["рекомендуемая_производительность_вытяжки"] = get_fact_slot(
                            fact, "рекомендуемая_производительность_вытяжки"
                        )
                        calculation_data["рекомендуемый_диаметр"] = get_fact_slot(
                            fact, "рекомендуемый_диаметр"
                        )

                    elif "рекомендация" in template_name:
                        try:
                            # Получаем элементы и объяснение
                            items_result = get_fact_slot(fact, "элементы")
                            explanation_result = get_fact_slot(fact, "объяснение")

                            # Обработка элементов (может быть список или кортеж)
                            if isinstance(items_result, (list, tuple)):
                                items_list = [str(item) for item in items_result]
                            else:
                                items_list = [str(items_result)] if items_result else []

                            # Обработка объяснения
                            if isinstance(explanation_result, (list, tuple)):
                                explanation_str = " ".join(str(exp) for exp in explanation_result)
                            else:
                                explanation_str = str(explanation_result) if explanation_result else ""

                            items_str = ", ".join(items_list) if items_list else ""

                            if items_str or explanation_str:
                                recommendations.append({
                                    "items": items_str,
                                    "explanation": explanation_str
                                })
                        except Exception as e:
                            print(f"Ошибка обработки рекомендации: {e}", file=sys.stderr)

                    elif "ошибка" in template_name:
                        try:
                            errors.append({
                                "код": get_fact_slot(fact, "код"),
                                "описание": get_fact_slot(fact, "описание")
                            })
                        except:
                            pass
                except Exception as e:
                    print(f"Ошибка при обработке факта: {e}", file=sys.stderr)
                    continue

            # Добавляем расчет в список, если есть данные
            if calculation_data:
                calculations.append(calculation_data)

            trace = mystdout.getvalue()

        except Exception as e:
            errors.append({
                "код": "SYS_ERR",
                "описание": f"Системная ошибка: {str(e)}"
            })
            trace = f"Ошибка выполнения: {str(e)}"
        finally:
            sys.stdout = old_stdout

    return render_template("index.html",
                           recommendations=recommendations,
                           trace=trace,
                           calculations=calculations,
                           errors=errors,
                           form_data=request.form if request.method == "POST" else {})


if __name__ == "__main__":
    app.run(debug=True, port=5000)