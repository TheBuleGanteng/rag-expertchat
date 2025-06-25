import { updateProfileForm } from './utils.js'

document.addEventListener('DOMContentLoaded', function() {
    console.log(`running slider_updates.js ... DOM content loaded`);
    console.log(`running sider_updates.js ... current origin is: ${ window.location.origin }`);

    function toPercentage(value) {
        return (value * 100).toFixed(0) + '%';
    }

    // Format number with commas
    function toNumberWithCommas(number) {
        return Number(number).toLocaleString();
    }

    // Slider management: Data source  ----------------------------------------------
    const chatHistoryRadioButtonOff = document.getElementById('chatHistoryRadioButtonOff');
    const generalKnowledgeRadioButtonOff = document.getElementById('generalKnowledgeRadioButtonOff');
    const generalKnowledgeRadioButtonOn = document.getElementById('generalKnowledgeRadioButtonOn');
    
    
    if (chatHistoryRadioButtonOff) {
        // Define the listener and what happens when a change is detected in chatHistoryRadioButtonOff
        chatHistoryRadioButtonOff.addEventListener('change', function () {
            console.log(`running aichat.js ... chatHistoryRadioButtonOff changed to ${ chatHistoryRadioButtonOff.checked }`)
        });

        // Define the listener and what happens when a change is detected in generalKnowledgeRadioButtonOff
        generalKnowledgeRadioButtonOff.addEventListener('change', function () {
            console.log(`running aichat.js ... generalKnowledgeRadioButtonOff changed to ${ generalKnowledgeRadioButtonOff.checked }`)
        });

        // Define the listener and what happens when a change is detected in generalKnowledgeRadioButtonOn
        generalKnowledgeRadioButtonOn.addEventListener('change', function () {
            console.log(`running aichat.js ... generalKnowledgeRadioButtonOn changed to ${ generalKnowledgeRadioButtonOn.checked }`)
        });
    }


    // Slider management: Number of experts  ----------------------------------------------
    const suggestExpertsSwitchElements = document.getElementsByName('suggest_experts');    
    const numberOfExpertsElements = document.getElementsByName('experts_suggested_number');
    const numberOfExpertsValueBoxElements = document.getElementsByName('number-of-experts-value-box');
    const expertSpeaksMyLangCheckboxElements = document.getElementsByName('expert_speaks_my_lang');
    const expertRecommendationSliderElements = document.getElementsByName('expert-recommendation-slider');
    const expertSuggestionConfigsDiv = document.getElementById('expert-suggestion-configs');

    console.log(`running sider_updates.js ... found ${suggestExpertsSwitchElements.length} suggestExpertsSwitchElements`);
    console.log(`running sider_updates.js ... found ${numberOfExpertsElements.length} numberOfExpertsElements`);
    console.log(`running sider_updates.js ... found ${numberOfExpertsValueBoxElements.length} numberOfExpertsValueBoxElements`);
    console.log(`running sider_updates.js ... found ${expertSpeaksMyLangCheckboxElements.length} expertSpeaksMyLangCheckboxElements`);
    console.log(`running sider_updates.js ... found ${expertRecommendationSliderElements.length} expertRecommendationSliderElements`);
    
    
    // Update the value box in response to a change in the slider
    function setExpertSliderListeners() {
        for (let j = 0; j < numberOfExpertsElements.length; j++) {
            numberOfExpertsValueBoxElements[j].innerHTML = numberOfExpertsElements[j].value
            numberOfExpertsElements[j].addEventListener('input', function() {
                for (let k = 0; k < numberOfExpertsValueBoxElements.length; k++) {
                    numberOfExpertsValueBoxElements[k].innerHTML = numberOfExpertsElements[j].value;
                }
            });
        }
    }

    // If 'suggestExpertsSwitchElements is not checked, disable the (1) number of experts (2) expert speaks my language and (3) recommendation sliders 
    if (suggestExpertsSwitchElements.length > 0) {
        for (let i = 0; i < suggestExpertsSwitchElements.length; i++) {
            
            const isChecked = suggestExpertsSwitchElements[i].checked;
            expertSuggestionConfigsDiv.style.display = isChecked ? 'block' : 'none';

            // At time of load, disable/enable 'number of experts' based on whether 'recommend experts' is ticked
            for (let j = 0; j < numberOfExpertsElements.length; j++) {
                numberOfExpertsElements[j].disabled = !isChecked;
                //numberOfExpertsElements[j].value = isChecked ? numberOfExpertsElements[j].value : 0;
            }
            // At time of load, disable/enable 'expert speaks my language' based on whether 'recommend experts' is ticked
            for (let j = 0; j < expertSpeaksMyLangCheckboxElements.length; j++) {
                expertSpeaksMyLangCheckboxElements[j].disabled = !isChecked;
            }
            // At time of load, disable/enable 'expert recommendation sliders' based on whether 'recommend experts' is ticked
            for (let j = 0; j < expertRecommendationSliderElements.length; j++) {
                // This targets the actual form field inside the 'expert-recommendation-slider' div at point j
                const sliderInput = expertRecommendationSliderElements[j].querySelector('input'); // Target the input element inside the div
                if (sliderInput) {
                    sliderInput.disabled = !isChecked;
                }
            }


            // Sets listeners in case ticked status changes
            suggestExpertsSwitchElements[i].addEventListener('change', function() {
                const isChecked = suggestExpertsSwitchElements[i].checked;
                expertSuggestionConfigsDiv.style.display = isChecked ? 'block' : 'none';

                // Update the 'number of experts suggested' to enabled/disabled, based on change in status of 'recommend experts'
                for (let j = 0; j < numberOfExpertsElements.length; j++) {
                    numberOfExpertsElements[j].disabled = !isChecked; // No. experts disabled if checked, enabled if not checked
                    //numberOfExpertsElements[j].value = isChecked ? 4 : 0; // No. experts 4 if checked, 0 if not checked
                    
                }
                // Update the 'expert speaks my language' to enabled/disabled, based on change in status of 'recommend experts'
                for (let j = 0; j < expertSpeaksMyLangCheckboxElements.length; j++) {
                    expertSpeaksMyLangCheckboxElements[j].disabled = !isChecked;
                    
                }
                // Update the 'expert recommendation sliders' to enabled/disabled, based on change in status of 'recommend experts'
                for (let j = 0; j < expertRecommendationSliderElements.length; j++) {
                    // This targets the actual form field inside the 'expert-recommendation-slider' div at point j
                    const sliderInput = expertRecommendationSliderElements[j].querySelector('input'); // Target the input element inside the div
                    if (sliderInput) {
                        sliderInput.disabled = !isChecked;
                    }
                }
                setExpertSliderListeners();
            });
        }
    } else {
        console.log(`running slider_updates.js ... no instances of suggestExpertsSwitchElements detected`);
    }

    // Initial call to set the initial value and event listener that will detect if any slider values change
    setExpertSliderListeners();


    // Slider management: Weight: years ----------------------------------------------
    const weightYearsElements = document.getElementsByName('weight_years');
    const weightYearsValueBoxElements = document.getElementsByName('recommendation-weight-years-value-box');

    console.log(`running sider_updates.js ... weightYearsElements.length is: ${weightYearsElements.length} `);
    console.log(`running sider_updates.js ... weightYearsValueBoxElements.length is: ${weightYearsValueBoxElements.length}`);
    
    function setYearsSliderListeners() {
        for (let j = 0; j < weightYearsElements.length; j++) {
            weightYearsValueBoxElements[j].innerHTML = weightYearsElements[j].value
            console.log(`running sider_updates.js ... weightYearsValueBoxElements[j].innerHTML set to: ${weightYearsValueBoxElements[j].innerHTML}`);
            
            weightYearsElements[j].addEventListener('input', function() {
                for (let k = 0; k < weightYearsValueBoxElements.length; k++) {
                    weightYearsValueBoxElements[k].innerHTML = weightYearsElements[j].value;
                    console.log(`running sider_updates.js ... weightYearsValueBoxElements[k].innerHTML set to: ${weightYearsValueBoxElements[k].innerHTML}`);
                }
            });
        }
    }

    // Initial call to set the initial value and event listener that will detect if any slider values change
    setYearsSliderListeners();


    // Slider management: Weight: industry ----------------------------------------------
    const weightIndustryElements = document.getElementsByName('weight_industry');
    const weightIndustryValueBoxElements = document.getElementsByName('recommendation-weight-industry-value-box');

    console.log(`running sider_updates.js ... weightIndustryElements.length is: ${weightIndustryElements.length} `);
    console.log(`running sider_updates.js ... weightIndustryValueBoxElements.length is: ${weightIndustryValueBoxElements.length}`);

    function setIndustrySliderListeners() {
        for (let j = 0; j < weightIndustryElements.length; j++) {
            weightIndustryValueBoxElements[j].innerHTML = weightIndustryElements[j].value;
            console.log(`running sider_updates.js ... weightIndustryValueBoxElements[j].innerHTML set to: ${weightIndustryValueBoxElements[j].innerHTML}`);
            
            weightIndustryElements[j].addEventListener('input', function() {
                for (let k = 0; k < weightIndustryValueBoxElements.length; k++) {
                    weightIndustryValueBoxElements[k].innerHTML = weightIndustryElements[j].value;
                    console.log(`running sider_updates.js ... weightIndustryValueBoxElements[k].innerHTML set to: ${weightIndustryValueBoxElements[k].innerHTML}`);
                }
            });
        }
    }

    // Initial call to set the initial value and event listener that will detect if any slider values change
    setIndustrySliderListeners();




    // Slider management: Weight: role ----------------------------------------------
    const weightRoleElements = document.getElementsByName('weight_role');
    const weightRoleValueBoxElements = document.getElementsByName('recommendation-weight-role-value-box');

    console.log(`running sider_updates.js ... weightRoleElements.length is: ${weightRoleElements.length} `);
    console.log(`running sider_updates.js ... weightRoleValueBoxElements.length is: ${weightRoleValueBoxElements.length}`);

    function setRoleSliderListeners() {
        for (let j = 0; j < weightRoleElements.length; j++) {
            weightRoleValueBoxElements[j].innerHTML = weightRoleElements[j].value;
            console.log(`running sider_updates.js ... weightRoleValueBoxElements[j].innerHTML set to: ${weightRoleValueBoxElements[j].innerHTML}`);
            
            weightRoleElements[j].addEventListener('input', function() {
                for (let k = 0; k < weightRoleValueBoxElements.length; k++) {
                    weightRoleValueBoxElements[k].innerHTML = weightRoleElements[j].value;
                    console.log(`running sider_updates.js ... weightRoleValueBoxElements[k].innerHTML set to: ${weightRoleValueBoxElements[k].innerHTML}`);
                }
            });
        }
    }

    // Initial call to set the initial value and event listener that will detect if any slider values change
    setRoleSliderListeners();





    // Slider management: Weight: topic ----------------------------------------------
    const weightTopicElements = document.getElementsByName('weight_topic');
    const weightTopicValueBoxElements = document.getElementsByName('recommendation-weight-topic-value-box');

    console.log(`running sider_updates.js ... weightTopicElements.length is: ${weightTopicElements.length} `);
    console.log(`running sider_updates.js ... weightTopicValueBoxElements.length is: ${weightTopicValueBoxElements.length}`);

    function setTopicSliderListeners() {
        for (let j = 0; j < weightTopicElements.length; j++) {
            weightTopicValueBoxElements[j].innerHTML = weightTopicElements[j].value;
            console.log(`running sider_updates.js ... weightTopicValueBoxElements[j].innerHTML set to: ${weightTopicValueBoxElements[j].innerHTML}`);
            
            weightTopicElements[j].addEventListener('input', function() {
                for (let k = 0; k < weightTopicValueBoxElements.length; k++) {
                    weightTopicValueBoxElements[k].innerHTML = weightTopicElements[j].value;
                    console.log(`running sider_updates.js ... weightTopicValueBoxElements[k].innerHTML set to: ${weightTopicValueBoxElements[k].innerHTML}`);
                }
            });
        }
    }

    // Initial call to set the initial value and event listener that will detect if any slider values change
    setTopicSliderListeners();





    // Slider management: Weight: geography ----------------------------------------------
    const weightGeographyElements = document.getElementsByName('weight_geography');
    const weightGeographyValueBoxElements = document.getElementsByName('recommendation-weight-geography-value-box');

    console.log(`running sider_updates.js ... weightGeographyElements.length is: ${weightGeographyElements.length} `);
    console.log(`running sider_updates.js ... weightGeographyValueBoxElements.length is: ${weightGeographyValueBoxElements.length}`);

    function setGeographySliderListeners() {
        for (let j = 0; j < weightGeographyElements.length; j++) {
            weightGeographyValueBoxElements[j].innerHTML = weightGeographyElements[j].value;
            console.log(`running sider_updates.js ... weightGeographyValueBoxElements[j].innerHTML set to: ${weightGeographyValueBoxElements[j].innerHTML}`);
            
            weightGeographyElements[j].addEventListener('input', function() {
                for (let k = 0; k < weightGeographyValueBoxElements.length; k++) {
                    weightGeographyValueBoxElements[k].innerHTML = weightGeographyElements[j].value;
                    console.log(`running sider_updates.js ... weightGeographyValueBoxElements[k].innerHTML set to: ${weightGeographyValueBoxElements[k].innerHTML}`);
                }
            });
        }
    }

    // Initial call to set the initial value and event listener that will detect if any slider values change
    setGeographySliderListeners();




    // Slider management: response length ----------------------------------------------
    const responseLengthElements = document.getElementsByName('response_length');
    const responseLengthValueBoxElements = document.getElementsByName('response-length-value-box');

    console.log(`running sider_updates.js ... responseLengthElements.length is: ${responseLengthElements.length} `);
    console.log(`running sider_updates.js ... responseLengthValueBoxElements.length is: ${responseLengthValueBoxElements.length}`);

    function setResponseLengthSliderListeners() {
        for (let j = 0; j < responseLengthElements.length; j++) {
            responseLengthValueBoxElements[j].innerHTML = responseLengthElements[j].value;
            console.log(`running sider_updates.js ... responseLengthValueBoxElements[j].innerHTML set to: ${responseLengthValueBoxElements[j].innerHTML}`);
            
            responseLengthElements[j].addEventListener('input', function() {
                for (let k = 0; k < responseLengthValueBoxElements.length; k++) {
                    responseLengthValueBoxElements[k].innerHTML = responseLengthElements[j].value;
                    console.log(`running sider_updates.js ... responseLengthValueBoxElements[k].innerHTML set to: ${responseLengthValueBoxElements[k].innerHTML}`);
                }
            });
        }
    }

    // Initial call to set the initial value and event listener that will detect if any slider values change
    setResponseLengthSliderListeners();




    // Slider management: chat history window ----------------------------------------------
    const chatHistorySliderElements = document.getElementsByName('chat_history_window');
    const chatHistoryValueBoxElements = document.getElementsByName('chat-history-window-value-box');
    const dataSourceFormElements = document.getElementsByName('data_source');
    const noChatHistory = document.querySelector('input[name="data_source"][value="rag"]');
    const chatHistoryWindowDiv = document.getElementById('chat-history-window-div');

    if (chatHistorySliderElements.length > 0 && chatHistoryValueBoxElements.length > 0) {
        
        // At page load, update the value and shown/hidden property of chat history, relative to noChatHistory
        if (noChatHistory) {
            if (noChatHistory.checked) {
                chatHistoryWindowDiv.style.display = 'none';
            } else {
                chatHistoryWindowDiv.style.display = '';
            }
        }

        // At page load, populate the chatHistoryValueBox
        chatHistorySliderElements.forEach((slider, index) => {
            chatHistoryValueBoxElements[index].innerHTML = slider.value;
        });
        
        // Add event listener for each chat history slider element
        chatHistorySliderElements.forEach((slider, index) => {
            slider.addEventListener('input', function () {
                chatHistoryValueBoxElements[index].innerHTML = slider.value;
            });
        });

        // Listen for changes to the data_source radio buttons
        dataSourceFormElements.forEach((radio) => {
            radio.addEventListener('change', function() {

                // Update each slider for a change in noChatHistory (eg. unchecked <-> checked)
                chatHistorySliderElements.forEach((slider, index) => {
                    if (noChatHistory.checked) {
                        slider.value = 1;
                        slider.disabled = true;
                        chatHistoryValueBoxElements[index].innerHTML = slider.value;
                        updateProfileForm(slider.name, slider.value);
                        chatHistoryWindowDiv.style.display = 'none';
                    } else {
                        slider.value = 5;
                        slider.disabled = false;
                        chatHistoryValueBoxElements[index].innerHTML = slider.value;
                        updateProfileForm(slider.name, slider.value);
                        chatHistoryWindowDiv.style.display = ''; // removes the display='none' applied above
                    }
                });
            });
        });
    }
    

    
    
    // Slider management: response temperature ----------------------------------------------
    const temperatureElements = document.getElementsByName('temperature');
    const temperatureValueBoxElements = document.getElementsByName('response-temperature-value-box');

    console.log(`running sider_updates.js ... temperatureElements.length is: ${temperatureElements.length} `);
    console.log(`running sider_updates.js ... temperatureValueBoxElements.length is: ${temperatureValueBoxElements.length}`);

    
    
    function setTemperatureSliderListeners() {
        for (let j = 0; j < temperatureElements.length; j++) {
            temperatureValueBoxElements[j].innerHTML = temperatureElements[j].value;
            console.log(`running sider_updates.js ... temperatureValueBoxElements[j].innerHTML set to: ${temperatureValueBoxElements[j].innerHTML}`);
            
            temperatureElements[j].addEventListener('input', function() {
                for (let k = 0; k < temperatureValueBoxElements.length; k++) {
                    temperatureValueBoxElements[k].innerHTML = temperatureElements[j].value;
                    console.log(`running sider_updates.js ... temperatureValueBoxElements[k].innerHTML set to: ${temperatureValueBoxElements[k].innerHTML}`);
                }
            });
        }
    }

    // Initial call to set the initial value and event listener that will detect if any slider values change
    setTemperatureSliderListeners();



    // Slider management: top_p ----------------------------------------------
    const topPElements = document.getElementsByName('top_p');
    const topPValueBoxElements = document.getElementsByName('top-p-value-box');

    console.log(`running sider_updates.js ... topPElements.length is: ${topPElements.length} `);
    console.log(`running sider_updates.js ... topPValueBoxElements.length is: ${topPValueBoxElements.length}`);

    
    
    function setTopPSliderListeners() {
        for (let j = 0; j < topPElements.length; j++) {
            topPValueBoxElements[j].innerHTML = topPElements[j].value;
            console.log(`running sider_updates.js ... topPValueBoxElements[j].innerHTML set to: ${topPValueBoxElements[j].innerHTML}`);
            
            topPElements[j].addEventListener('input', function() {
                for (let k = 0; k < topPValueBoxElements.length; k++) {
                    topPValueBoxElements[k].innerHTML = topPElements[j].value;
                    console.log(`running sider_updates.js ... topPValueBoxElements[k].innerHTML set to: ${topPValueBoxElements[k].innerHTML}`);
                }
            });
        }
    }

    // Initial call to set the initial value and event listener that will detect if any slider values change
    setTopPSliderListeners();




    // Slider management: chunk_size ----------------------------------------------
    const chunkSizeElements = document.getElementsByName('chunk_size');
    const chunkSizeValueBoxElements = document.getElementsByName('chunk-size-value-box');
    
    
    function setChunkSizeSliderListeners() {
        if (chunkSizeElements && chunkSizeValueBoxElements) {
            console.log(`running sider_updates.js ... chunkSizeElements.length is: ${chunkSizeElements.length} `);
            console.log(`running sider_updates.js ... chunkSizeValueBoxElements.length is: ${chunkSizeValueBoxElements.length}`);

            for (let j = 0; j < chunkSizeElements.length; j++) {
                chunkSizeValueBoxElements[j].innerHTML = toNumberWithCommas(chunkSizeElements[j].value);
                console.log(`running sider_updates.js ... chunkSizeValueBoxElements[j].innerHTML set to: ${chunkSizeValueBoxElements[j].innerHTML}`);
                
                chunkSizeElements[j].addEventListener('input', function() {
                    for (let k = 0; k < chunkSizeValueBoxElements.length; k++) {
                        chunkSizeValueBoxElements[k].innerHTML = toNumberWithCommas(chunkSizeElements[j].value);
                        console.log(`running sider_updates.js ... chunkSizeValueBoxElements[k].innerHTML set to: ${chunkSizeValueBoxElements[k].innerHTML}`);
                    }
                });
            }
        }
    }

    // Initial call to set the initial value and event listener that will detect if any slider values change
    setChunkSizeSliderListeners();





    // Slider management: chunk_overlap ----------------------------------------------
    const chunkOverlapElements = document.getElementsByName('chunk_overlap');
    const chunkOverlapValueBoxElements = document.getElementsByName('chunk-overlap-value-box');

    console.log(`running sider_updates.js ... chunkOverlapElements.length is: ${chunkOverlapElements.length} `);
    console.log(`running sider_updates.js ... chunkOverlapValueBoxElements.length is: ${chunkOverlapValueBoxElements.length}`);

    
    
    function setChunkOverlapSliderListeners() {
        for (let j = 0; j < chunkOverlapElements.length; j++) {
            chunkOverlapValueBoxElements[j].innerHTML = toPercentage(chunkOverlapElements[j].value);
            console.log(`running sider_updates.js ... chunkOverlapValueBoxElements[j].innerHTML set to: ${chunkOverlapValueBoxElements[j].innerHTML}`);
            
            chunkOverlapElements[j].addEventListener('input', function() {
                for (let k = 0; k < chunkOverlapValueBoxElements.length; k++) {
                    chunkOverlapValueBoxElements[k].innerHTML = toPercentage(chunkOverlapElements[j].value);
                    console.log(`running sider_updates.js ... chunkOverlapValueBoxElements[k].innerHTML set to: ${chunkOverlapValueBoxElements[k].innerHTML}`);
                }
            });
        }
    }

    // Initial call to set the initial value and event listener that will detect if any slider values change
    setChunkOverlapSliderListeners();




    // Slider management: langchain_k ----------------------------------------------
    const langchainKElements = document.getElementsByName('langchain_k');
    const langchainKValueBoxElements = document.getElementsByName('langchain-k-value-box');

    console.log(`running sider_updates.js ... langchainKElements.length is: ${langchainKElements.length} `);
    console.log(`running sider_updates.js ... langchainKValueBoxElements.length is: ${langchainKValueBoxElements.length}`);

    
    
    function setLangchainKSliderListeners() {
        for (let j = 0; j < langchainKElements.length; j++) {
            langchainKValueBoxElements[j].innerHTML = langchainKElements[j].value;
            console.log(`running sider_updates.js ... langchainKValueBoxElements[j].innerHTML set to: ${langchainKValueBoxElements[j].innerHTML}`);
            
            langchainKElements[j].addEventListener('input', function() {
                for (let k = 0; k < langchainKValueBoxElements.length; k++) {
                    langchainKValueBoxElements[k].innerHTML = langchainKElements[j].value;
                    console.log(`running sider_updates.js ... langchainKValueBoxElements[k].innerHTML set to: ${langchainKValueBoxElements[k].innerHTML}`);
                }
            });
        }
    }

    // Initial call to set the initial value and event listener that will detect if any slider values change
    setLangchainKSliderListeners();




    // Slider management: chat history window ----------------------------------------------
    const preprocessingSwitch = document.getElementById('preprocessing');    
    const preprocessingModelDiv = document.getElementById('preprocessing-model-div');
    const preprocessingModel = document.getElementById('preprocessing-model');

    // Group with other initialization code
    function initializePreprocessing() {
        if (preprocessingSwitch && preprocessingModelDiv && preprocessingModel) {
            function updateVisibility() {
                const isChecked = preprocessingSwitch.checked;
                console.log('Preprocessing switch state:', isChecked);
                
                preprocessingModelDiv.style.display = isChecked ? 'block' : 'none';
                preprocessingModel.disabled = !isChecked;
            }

            updateVisibility();  // Set initial state

            preprocessingSwitch.addEventListener('change', function() {
                console.log('Preprocessing switch changed');
                updateVisibility();
            });
        } else {
            console.log('Some preprocessing elements not found:', {
                switch: Boolean(preprocessingSwitch),
                div: Boolean(preprocessingModelDiv),
                model: Boolean(preprocessingModel)
            });
        }
    }

    // Call it with other initialization functions
    initializePreprocessing();


});